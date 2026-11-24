import math
import time
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

PERIOD_MAP = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
MARKET_SUFFIX = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": "", "NYSE": ""}
SOURCE_NAME = "Yahoo Finance (via yfinance)"
CACHE_TTL_SECONDS = 300

INCOME_ITEMS = [
    "Total Revenue", "Gross Profit", "Operating Income",
    "EBITDA", "Net Income", "Basic EPS", "Diluted EPS",
]
BALANCE_ITEMS = [
    "Total Assets", "Total Liabilities Net Minority Interest",
    "Stockholders Equity", "Total Debt", "Cash And Cash Equivalents", "Net Debt",
]
CASHFLOW_ITEMS = [
    "Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow",
    "Capital Expenditure", "Free Cash Flow",
]

_cache: dict = {}


class NoDataError(Exception):
    """Yahoo returned no usable data for this ticker."""


class ProviderError(Exception):
    """The data provider could not be reached or failed."""


def _cache_get(key):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    return None


def _cache_set(key, value):
    _cache[key] = (time.time(), value)
    return value


def _clean(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def to_yahoo_symbol(ticker: str, market: str) -> str:
    t = ticker.strip().upper()
    if t.endswith((".NS", ".BO")) or t.startswith("^"):
        return t
    return t + MARKET_SUFFIX[market]


def fetch_history(ticker: str, market: str, period: str) -> dict:
    symbol = to_yahoo_symbol(ticker, market)
    key = ("history", symbol, period)
    cached = _cache_get(key)
    if cached:
        return cached

    try:
        df = yf.Ticker(symbol).history(period=PERIOD_MAP[period], auto_adjust=False)
    except Exception as exc:
        raise ProviderError(f"Yahoo Finance request failed: {exc}") from exc

    if df is None or df.empty:
        raise NoDataError(
            f"No price data found for {symbol}. Check the ticker and the selected market."
        )

    rows_received = len(df)
    df = df.reset_index()
    df["date"] = df[df.columns[0]].dt.strftime("%Y-%m-%d")
    df = df[["date", "Open", "High", "Low", "Close", "Volume"]]

    before = len(df)
    df = df.drop_duplicates(subset="date", keep="last")
    duplicates_removed = before - len(df)

    before = len(df)
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    missing_removed = before - len(df)

    before = len(df)
    df = df[(df["High"] >= df["Low"]) & (df["Low"] > 0)]
    inconsistent_removed = before - len(df)

    if df.empty:
        raise NoDataError(f"No valid price data remained for {symbol} after validation.")

    df = df.copy()
    df["Volume"] = df["Volume"].fillna(0).astype("int64")

    prices = [
        {
            "date": r.date,
            "open": round(float(r.Open), 2),
            "high": round(float(r.High), 2),
            "low": round(float(r.Low), 2),
            "close": round(float(r.Close), 2),
            "volume": int(r.Volume),
        }
        for r in df.itertuples(index=False)
    ]

    result = {
        "ticker": ticker.strip().upper(),
        "symbol": symbol,
        "market": market,
        "period": period,
        "source": SOURCE_NAME,
        "retrieved_at": datetime.now(timezone.utc),
        "prices": prices,
        "validation": {
            "rows_received": rows_received,
            "rows_returned": len(prices),
            "duplicates_removed": duplicates_removed,
            "missing_removed": missing_removed,
            "inconsistent_removed": inconsistent_removed,
        },
    }
    return _cache_set(key, result)


def fetch_profile(ticker: str, market: str) -> dict:
    symbol = to_yahoo_symbol(ticker, market)
    key = ("profile", symbol)
    cached = _cache_get(key)
    if cached:
        return cached

    try:
        info = yf.Ticker(symbol).info
    except Exception as exc:
        raise ProviderError(f"Yahoo Finance request failed: {exc}") from exc

    name = (info or {}).get("longName") or (info or {}).get("shortName")
    if not info or not name:
        raise NoDataError(
            f"No company profile found for {symbol}. Check the ticker and the selected market."
        )

    profile = {
        "name": name,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "currency": info.get("currency"),
        "website": info.get("website"),
        "employees": info.get("fullTimeEmployees"),
        "summary": info.get("longBusinessSummary"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "price_to_book": info.get("priceToBook"),
        "return_on_equity": info.get("returnOnEquity"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
    }
    profile = {k: _clean(v) for k, v in profile.items()}

    result = {
        "ticker": ticker.strip().upper(),
        "symbol": symbol,
        "market": market,
        "source": SOURCE_NAME,
        "retrieved_at": datetime.now(timezone.utc),
        "profile": profile,
    }
    return _cache_set(key, result)


def _table(df, wanted):
    if df is None or df.empty:
        return {"periods": [], "rows": []}
    periods = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c) for c in df.columns]
    rows = []
    for label in wanted:
        if label in df.index:
            values = [None if pd.isna(v) else float(v) for v in df.loc[label].tolist()]
            rows.append({"item": label, "values": values})
    return {"periods": periods, "rows": rows}


def fetch_financials(ticker: str, market: str) -> dict:
    symbol = to_yahoo_symbol(ticker, market)
    key = ("financials", symbol)
    cached = _cache_get(key)
    if cached:
        return cached

    t = yf.Ticker(symbol)
    try:
        income = _table(t.income_stmt, INCOME_ITEMS)
        balance = _table(t.balance_sheet, BALANCE_ITEMS)
        cash = _table(t.cashflow, CASHFLOW_ITEMS)
    except Exception as exc:
        raise ProviderError(f"Yahoo Finance request failed: {exc}") from exc

    tables = {
        "income statement": income,
        "balance sheet": balance,
        "cash flow statement": cash,
    }
    if all(not tbl["rows"] for tbl in tables.values()):
        raise NoDataError(
            f"No financial statements are available for {symbol} from Yahoo Finance."
        )

    notes = [
        f"The {name} is not available from the provider for this company."
        for name, tbl in tables.items()
        if not tbl["rows"]
    ]

    try:
        currency = t.info.get("financialCurrency")
    except Exception:
        currency = None

    result = {
        "ticker": ticker.strip().upper(),
        "symbol": symbol,
        "market": market,
        "source": SOURCE_NAME,
        "retrieved_at": datetime.now(timezone.utc),
        "currency": currency,
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cash,
        "notes": notes,
    }
    return _cache_set(key, result)


def search_stocks(query: str) -> list[dict]:
    try:
        quotes = yf.Search(query, max_results=8).quotes
    except Exception as exc:
        raise ProviderError(f"Yahoo Finance search failed: {exc}") from exc

    results = []
    for q in quotes:
        if q.get("quoteType") not in ("EQUITY", "ETF"):
            continue
        results.append(
            {
                "symbol": q.get("symbol"),
                "name": q.get("longname") or q.get("shortname") or q.get("symbol"),
                "exchange": q.get("exchDisp") or q.get("exchange"),
            }
        )
    return results