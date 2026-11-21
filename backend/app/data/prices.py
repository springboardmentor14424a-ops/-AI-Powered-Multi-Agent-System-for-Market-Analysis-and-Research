"""Daily price history.

Order of preference:  fresh local cache -> Yahoo Finance (live) -> Kaggle NIFTY-50 CSV
(offline copy, NSE only). Raises DataUnavailable if none works.
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd

from ..config import settings
from ..stocks import provider_symbol
from . import DataUnavailable, data_dir

log = logging.getLogger(__name__)

COLUMNS = ["open", "high", "low", "close", "volume"]
CACHE_HOURS = 12
BENCHMARKS = {"NSE": "^NSEI", "BSE": "^BSESN", "NASDAQ": "^GSPC", "NYSE": "^GSPC"}


@dataclass
class PriceData:
    frame: pd.DataFrame  # DatetimeIndex (tz-naive, sorted), columns = COLUMNS
    symbol: str
    source: str
    retrieved_at: str | None = None  # when the provider was actually asked (UTC, ISO 8601)
    from_cache: bool = False
    cleaning: dict = field(default_factory=dict)  # what _clean removed (duplicates, empty rows)

    @property
    def last_date(self) -> pd.Timestamp:
        return self.frame.index[-1]


def history_days(days: int) -> int:
    """Calendar days to fetch: the analysis window plus enough history for the
    200-day moving average."""
    return max(days + 300, 420)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "close" not in df.columns:
        raise DataUnavailable("price data has no 'close' column")
    for col in ("open", "high", "low"):
        if col not in df.columns:
            df[col] = df["close"]
    if "volume" not in df.columns:
        df["volume"] = 0
    df = df[COLUMNS].apply(pd.to_numeric, errors="coerce")
    raw_rows = len(df)
    idx = pd.to_datetime(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)  # keep the exchange's calendar date
    df.index = idx.normalize()
    deduped = df[~df.index.duplicated(keep="last")].sort_index()
    df = deduped.dropna(subset=["close"])
    if df.empty:
        raise DataUnavailable("price data is empty")
    df.attrs["cleaning"] = {
        "raw_rows": raw_rows,
        "duplicate_dates_removed": raw_rows - len(deduped),
        "rows_without_close_removed": len(deduped) - len(df),
    }
    return df


def _cache_path(symbol: str, need: int):
    return data_dir("cache", "prices", f"{symbol.replace('^', '_')}_{need}.csv")


def _read_cache(symbol: str, need: int) -> pd.DataFrame | None:
    path = _cache_path(symbol, need)
    try:
        if not path.exists() or (time.time() - path.stat().st_mtime) / 3600 > CACHE_HOURS:
            return None
        return _clean(pd.read_csv(path, index_col=0, parse_dates=True))
    except Exception:  # a corrupt cache file is just a cache miss
        return None


def _meta_path(symbol: str, need: int):
    return _cache_path(symbol, need).with_suffix(".meta.json")


def _write_cache(symbol: str, need: int, df: pd.DataFrame, source: str = "", retrieved_at: str = "") -> None:
    try:
        path = _cache_path(symbol, need)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path)
        # Remember where the data came from and when, so a later cache hit still reports it.
        _meta_path(symbol, need).write_text(
            json.dumps({"source": source, "retrieved_at": retrieved_at, "cleaning": df.attrs.get("cleaning", {})})
        )
    except OSError:
        log.warning("Could not write price cache for %s", symbol)


def _read_meta(symbol: str, need: int) -> dict:
    try:
        return json.loads(_meta_path(symbol, need).read_text())
    except (OSError, ValueError):
        return {}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_live(symbol: str, need: int) -> pd.DataFrame:
    """Download daily prices from Yahoo Finance via yfinance."""
    try:
        import yfinance as yf

        start = (datetime.now() - timedelta(days=need)).strftime("%Y-%m-%d")
        raw = yf.Ticker(symbol).history(
            start=start, interval="1d", auto_adjust=True, timeout=settings.HTTP_TIMEOUT
        )
    except Exception as e:
        log.warning("Yahoo Finance request failed for %s: %s", symbol, e)  # details for the log only
        raise DataUnavailable(f"Could not download prices for {symbol} from Yahoo Finance (offline or blocked).") from e
    if raw is None or raw.empty:
        raise DataUnavailable(f"Yahoo Finance returned no data for {symbol}")
    return _clean(raw)


def load_nifty50(ticker: str, need: int) -> pd.DataFrame:
    """Offline fallback: Kaggle 'NIFTY-50 Stock Market Data' (one CSV per company)."""
    root = data_dir("raw", "nifty50")
    path = None
    if root.exists():
        path = next((p for p in root.rglob("*.csv") if p.stem.upper() == ticker.upper()), None)
    if path is None:
        raise DataUnavailable(f"{ticker} is not in the offline NIFTY-50 dataset")
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" not in df.columns:
        raise DataUnavailable(f"{path.name} has no Date column")
    df.index = pd.to_datetime(df.pop("date"), errors="coerce")
    df = _clean(df[df.index.notna()])
    return df[df.index >= df.index[-1] - timedelta(days=need)]


def get_prices(market: str, ticker: str, days: int) -> PriceData:
    symbol = provider_symbol(market, ticker)
    need = history_days(days)

    cached = _read_cache(symbol, need)
    if cached is not None:
        meta = _read_meta(symbol, need)
        cached.attrs["cleaning"] = meta.get("cleaning", {})
        return PriceData(
            cached,
            symbol,
            "Yahoo Finance (cached)",
            retrieved_at=meta.get("retrieved_at") or None,
            from_cache=True,
            cleaning=meta.get("cleaning", {}),
        )

    try:
        df = fetch_live(symbol, need)
        stamp = _now()
        _write_cache(symbol, need, df, "Yahoo Finance (yfinance)", stamp)
        return PriceData(df, symbol, "Yahoo Finance (yfinance)", stamp, False, df.attrs.get("cleaning", {}))
    except DataUnavailable as live_error:
        if market == "NSE":
            try:
                df = load_nifty50(ticker, need)
                return PriceData(
                    df,
                    symbol,
                    f"Kaggle NIFTY-50 dataset (offline copy, ends {df.index[-1]:%Y-%m-%d})",
                    _now(),
                    False,
                    df.attrs.get("cleaning", {}),
                )
            except DataUnavailable:
                pass
        raise live_error


def get_benchmark(market: str, days: int) -> PriceData:
    """Market index used to compute beta."""
    symbol = BENCHMARKS[market]
    need = history_days(days)
    cached = _read_cache(symbol, need)
    if cached is not None:
        return PriceData(cached, symbol, "Yahoo Finance (cached)", from_cache=True)
    df = fetch_live(symbol, need)
    stamp = _now()
    _write_cache(symbol, need, df, "Yahoo Finance (yfinance)", stamp)
    return PriceData(df, symbol, "Yahoo Finance (yfinance)", stamp)
