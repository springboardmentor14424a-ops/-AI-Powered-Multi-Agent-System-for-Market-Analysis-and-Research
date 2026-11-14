"""Daily price history.

Order of preference:  fresh local cache -> Yahoo Finance (live) -> Kaggle NIFTY-50 CSV
(offline copy, NSE only). Raises DataUnavailable if none works.
"""
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

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
    idx = pd.to_datetime(df.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)  # keep the exchange's calendar date
    df.index = idx.normalize()
    df = df[~df.index.duplicated(keep="last")].sort_index().dropna(subset=["close"])
    if df.empty:
        raise DataUnavailable("price data is empty")
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


def _write_cache(symbol: str, need: int, df: pd.DataFrame) -> None:
    try:
        path = _cache_path(symbol, need)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path)
    except OSError:
        log.warning("Could not write price cache for %s", symbol)


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
        return PriceData(cached, symbol, "Yahoo Finance (cached today)")

    try:
        df = fetch_live(symbol, need)
        _write_cache(symbol, need, df)
        return PriceData(df, symbol, "Yahoo Finance (yfinance)")
    except DataUnavailable as live_error:
        if market == "NSE":
            try:
                df = load_nifty50(ticker, need)
                return PriceData(
                    df, symbol, f"Kaggle NIFTY-50 dataset (offline copy, ends {df.index[-1]:%Y-%m-%d})"
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
        return PriceData(cached, symbol, "Yahoo Finance (cached today)")
    df = fetch_live(symbol, need)
    _write_cache(symbol, need, df)
    return PriceData(df, symbol, "Yahoo Finance (yfinance)")
