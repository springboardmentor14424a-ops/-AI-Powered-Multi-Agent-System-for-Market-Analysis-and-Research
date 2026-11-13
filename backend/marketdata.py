"""Point 2: stock search and market data collection (data comes from Yahoo Finance)."""
import hashlib
import json
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

SOURCE_NAME = "Yahoo Finance (via yfinance)"
PERIODS = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}

_CACHE: dict = {}
CACHE_SECONDS = 600  # reuse the same answer for 10 minutes to avoid hammering Yahoo


class MarketDataError(Exception):
    """Raised when Yahoo has nothing for us or cannot be reached."""


def _cached(key, loader):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1], True
    value = loader()
    _CACHE[key] = (time.time(), value)
    return value, False


def _retry(fn, attempts=2):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # network trouble, rate limits, bad symbol ...
            last = exc
            time.sleep(1.0 * (i + 1))
    raise MarketDataError(f"Could not get data from Yahoo Finance right now ({type(last).__name__}). Please try again.")


def normalize_ticker(ticker: str, market: str) -> str:
    """TCS + NSE -> TCS.NS, TCS + BSE -> TCS.BO, AAPL + NASDAQ -> AAPL."""
    t = ticker.strip().upper()
    if market in ("NSE", "BSE") and not (t.endswith(".NS") or t.endswith(".BO")):
        t += SUFFIX[market]
    return t


def _market_of(quote: dict) -> str:
    ex = (quote.get("exchange") or "").upper()
    disp = (quote.get("exchDisp") or "").lower()
    if ex in {"NSI"} or "nse" in disp or "national stock exchange" in disp:
        return "NSE"
    if ex in {"BSE", "BOM"} or "bse" in disp or "bombay" in disp:
        return "BSE"
    if ex in {"NMS", "NGM", "NCM"} or "nasdaq" in disp:
        return "NASDAQ"
    if ex in {"NYQ"} or "nyse" in disp or "new york" in disp:
        return "NYSE"
    return quote.get("exchDisp") or ex or "Other"


def search_stocks(query: str, market: str | None = None) -> list[dict]:
    query = query.strip()
    if len(query) < 2:
        return []

    def load():
        quotes = _retry(lambda: yf.Search(query, max_results=20, news_count=0, lists_count=0).quotes)
        out = []
        for q in quotes:
            if q.get("quoteType") not in ("EQUITY", "ETF"):
                continue
            out.append({
                "ticker": q.get("symbol"),
                "name": q.get("longname") or q.get("shortname") or q.get("symbol"),
                "market": _market_of(q),
                "type": q.get("quoteType"),
            })
        return out

    results, _ = _cached(("search", query.lower()), load)
    if market:
        preferred = [r for r in results if r["market"] == market]
        others = [r for r in results if r["market"] != market]
        results = preferred + others  # chosen market first, never hide the rest
    return results[:10]


def clean_ohlcv(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate price data: duplicates, missing values and impossible prices."""
    if df is None or df.empty:
        raise MarketDataError("No price data was found for this ticker and period.")

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    idx = pd.to_datetime(df.index)
    if getattr(idx, "tz", None) is not None:
        idx = idx.tz_localize(None)
    df.index = idx.normalize()
    df.index.name = "date"

    report = {"rows_received": int(len(df))}

    dup = df.index.duplicated(keep="last")
    report["duplicate_dates_removed"] = int(dup.sum())
    df = df[~dup]

    price_cols = ["Open", "High", "Low", "Close"]
    missing = df[price_cols].isna().any(axis=1)
    report["rows_with_missing_prices_removed"] = int(missing.sum())
    df = df[~missing]

    report["missing_volume_filled_with_zero"] = int(df["Volume"].isna().sum())
    df["Volume"] = df["Volume"].fillna(0)

    bad = (
        (df["High"] < df["Low"])
        | (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
        | (df["Open"] > df["High"]) | (df["Open"] < df["Low"])
        | (df[price_cols] <= 0).any(axis=1)
        | (df["Volume"] < 0)
    )
    report["inconsistent_rows_removed"] = int(bad.sum())
    df = df[~bad].sort_index()

    if df.empty:
        raise MarketDataError("All price rows failed validation, so nothing can be shown.")

    report["rows_kept"] = int(len(df))
    report["first_date"] = df.index[0].strftime("%Y-%m-%d")
    report["last_date"] = df.index[-1].strftime("%Y-%m-%d")
    removed = report["rows_received"] - report["rows_kept"]
    report["warnings"] = [f"{removed} row(s) were removed during validation."] if removed else []
    return df, report


def get_history(ticker: str, period: str) -> dict:
    if period not in PERIODS:
        raise MarketDataError("Unsupported analysis period.")

    def load():
        raw = _retry(lambda: yf.Ticker(ticker).history(period=PERIODS[period], interval="1d", auto_adjust=False))
        df, report = clean_ohlcv(raw)
        rows = [
            {
                "date": d.strftime("%Y-%m-%d"),
                "open": round(float(r.Open), 2), "high": round(float(r.High), 2),
                "low": round(float(r.Low), 2), "close": round(float(r.Close), 2),
                "volume": int(r.Volume),
            }
            for d, r in df.iterrows()
        ]
        return {
            "ticker": ticker,
            "period": period,
            "rows": rows,
            "validation": report,
            "source": {
                "name": SOURCE_NAME,
                "url": f"https://finance.yahoo.com/quote/{ticker}",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    data, from_cache = _cached(("history", ticker, period), load)
    data = {**data, "from_cache": from_cache}
    return data


def content_hash(data: dict) -> str:
    return hashlib.sha256(json.dumps(data["rows"], sort_keys=True).encode()).hexdigest()


def get_profile(ticker: str) -> dict:
    def load():
        info = _retry(lambda: yf.Ticker(ticker).info) or {}
        summary = info.get("longBusinessSummary") or ""
        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "exchange": info.get("fullExchangeName") or info.get("exchange"),
            "website": info.get("website"),
            "market_cap": info.get("marketCap"),
            "summary": (summary[:600] + "...") if len(summary) > 600 else summary,
        }

    data, _ = _cached(("profile", ticker), load)
    return data
