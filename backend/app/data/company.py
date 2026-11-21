"""Company profile and annual financial statements.

Profile      Yahoo Finance (yfinance .info)  ->  built-in ticker list (name/market only)
Statements   Yahoo Finance annual statements  ->  SEC EDGAR 10-K figures (US, needs SEC_USER_AGENT)

Both results carry their source and retrieval time, and are cached for 24 hours.
"""
import json
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..config import settings
from ..stocks import find_stock, provider_symbol
from . import DataUnavailable, data_dir
from . import fundamentals as fund

log = logging.getLogger(__name__)
CACHE_HOURS = 24


@dataclass
class CompanyData:
    payload: dict
    source: str
    retrieved_at: str
    from_cache: bool = False
    notes: list[str] = field(default_factory=list)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _num(x):
    """JSON-safe number: NaN/inf/non-numbers become None."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or math.isinf(f) else f


# ------------------------------------------------------------------ cache

def _cache_file(symbol: str, kind: str):
    return data_dir("cache", "company", f"{symbol.replace('^', '_')}_{kind}.json")


def _read(symbol: str, kind: str) -> CompanyData | None:
    path = _cache_file(symbol, kind)
    try:
        if not path.exists() or (time.time() - path.stat().st_mtime) / 3600 > CACHE_HOURS:
            return None
        d = json.loads(path.read_text())
        return CompanyData(d["payload"], d["source"], d["retrieved_at"], True, d.get("notes", []))
    except (OSError, ValueError, KeyError):
        return None


def _write(symbol: str, kind: str, c: CompanyData) -> None:
    try:
        path = _cache_file(symbol, kind)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"payload": c.payload, "source": c.source,
                                    "retrieved_at": c.retrieved_at, "notes": c.notes}))
    except OSError:
        log.warning("Could not write company cache for %s", symbol)


# ------------------------------------------------------------------ profile

PROFILE_FIELDS = {
    "name": "longName",
    "sector": "sector",
    "industry": "industry",
    "country": "country",
    "city": "city",
    "website": "website",
    "employees": "fullTimeEmployees",
    "currency": "currency",
    "exchange": "fullExchangeName",
    "market_cap": "marketCap",
    "summary": "longBusinessSummary",
}


def _yf_profile(symbol: str) -> dict:
    try:
        import yfinance as yf

        info = yf.Ticker(symbol).info
    except Exception as e:
        log.warning("Yahoo Finance profile request failed for %s: %s", symbol, e)
        raise DataUnavailable("Could not download the company profile from Yahoo Finance.") from e
    if not info or len(info) < 5:
        raise DataUnavailable(f"Yahoo Finance has no profile for {symbol}")
    out = {}
    for key, src in PROFILE_FIELDS.items():
        val = info.get(src)
        if key in ("market_cap", "employees"):
            val = _num(val)
        out[key] = val if val not in ("", None) else None
    return out


def get_profile(market: str, ticker: str) -> CompanyData:
    symbol = provider_symbol(market, ticker)
    cached = _read(symbol, "profile")
    if cached:
        return cached
    notes: list[str] = []
    try:
        payload = _yf_profile(symbol)
        result = CompanyData(payload, "Yahoo Finance (yfinance)", _now())
    except DataUnavailable as e:
        stock = find_stock(market, ticker)
        if stock is None:
            raise
        notes.append(f"{e} Showing basic details from the built-in stock list only.")
        payload = {k: None for k in PROFILE_FIELDS}
        payload["name"] = stock["company_name"]
        payload["exchange"] = market
        result = CompanyData(payload, "Built-in stock list", _now(), notes=notes)
    missing = [k for k, v in result.payload.items() if v is None]
    if missing:
        result.notes.append("Not available from the source: " + ", ".join(missing) + ".")
    if result.source.startswith("Yahoo"):
        _write(symbol, "profile", result)
    return result


# ------------------------------------------------------------------ statements

# (label, yfinance row names to try)
_INCOME = [("Total revenue", ["Total Revenue", "Operating Revenue"]),
           ("Gross profit", ["Gross Profit"]),
           ("Operating income", ["Operating Income"]),
           ("EBITDA", ["EBITDA"]),
           ("Net income", ["Net Income", "Net Income Common Stockholders"]),
           ("Diluted EPS", ["Diluted EPS"])]
_BALANCE = [("Total assets", ["Total Assets"]),
            ("Total liabilities", ["Total Liabilities Net Minority Interest"]),
            ("Stockholders' equity", ["Stockholders Equity", "Total Equity Gross Minority Interest"]),
            ("Total debt", ["Total Debt"]),
            ("Cash and equivalents", ["Cash And Cash Equivalents"])]
_CASH = [("Operating cash flow", ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"]),
         ("Investing cash flow", ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"]),
         ("Financing cash flow", ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"]),
         ("Capital expenditure", ["Capital Expenditure"]),
         ("Free cash flow", ["Free Cash Flow"])]


def _frame_to_rows(df, wanted) -> tuple[list[str], list[dict]]:
    """DataFrame (rows = line items, columns = period ends) -> (periods, rows newest first)."""
    if df is None or getattr(df, "empty", True):
        return [], []
    cols = sorted(df.columns, reverse=True)
    periods = [c.strftime("%Y-%m-%d") if hasattr(c, "strftime") else str(c) for c in cols]
    rows = []
    for label, names in wanted:
        name = next((n for n in names if n in df.index), None)
        if name is None:
            continue
        values = [_num(df.loc[name, c]) for c in cols]
        if any(v is not None for v in values):
            rows.append({"item": label, "values": values})
    return periods, rows


def _yf_statements(symbol: str) -> dict:
    try:
        import yfinance as yf

        t = yf.Ticker(symbol)
        frames = {"income_statement": (t.income_stmt, _INCOME),
                  "balance_sheet": (t.balance_sheet, _BALANCE),
                  "cash_flow": (t.cashflow, _CASH)}
    except Exception as e:
        log.warning("Yahoo Finance statements request failed for %s: %s", symbol, e)
        raise DataUnavailable("Could not download financial statements from Yahoo Finance.") from e
    out = {}
    for key, (df, wanted) in frames.items():
        periods, rows = _frame_to_rows(df, wanted)
        if rows:
            out[key] = {"periods": periods, "rows": rows}
    if not out:
        raise DataUnavailable(f"Yahoo Finance has no financial statements for {symbol}")
    return out


def statements_from_companyfacts(facts: dict, years: int = 4) -> dict:
    """Annual figures from SEC 10-K filings (a subset of the full statements)."""
    def series(name):
        return dict(fund._annual_series(facts, fund._TAGS[name], name in fund._FLOW_ITEMS))

    s = {k: series(k) for k in fund._TAGS}
    out = {}
    for key, names in (("income_statement", [("Total revenue", "revenue"), ("Net income", "net_income")]),
                       ("balance_sheet", [("Total assets", "assets"), ("Total liabilities", "liabilities"),
                                          ("Stockholders' equity", "equity")])):
        ends = sorted({e for _, k in names for e in s[k]}, reverse=True)[:years]
        rows = []
        for label, k in names:
            values = [_num(s[k].get(e)) for e in ends]
            if any(v is not None for v in values):
                rows.append({"item": label, "values": values})
        if rows:
            out[key] = {"periods": ends, "rows": rows}
    if not out:
        raise DataUnavailable("EDGAR returned no usable annual figures")
    return out


def get_statements(market: str, ticker: str) -> CompanyData:
    symbol = provider_symbol(market, ticker)
    cached = _read(symbol, "statements")
    if cached:
        return cached
    notes: list[str] = []
    try:
        payload, source = _yf_statements(symbol), "Yahoo Finance (yfinance), annual statements"
    except DataUnavailable as yf_error:
        if market in ("NASDAQ", "NYSE") and settings.SEC_USER_AGENT:
            try:
                payload = statements_from_companyfacts(fund.get_edgar_facts(ticker))
                source = "SEC EDGAR company facts (10-K filings)"
                notes.append(f"{yf_error} Used SEC EDGAR instead (revenue, net income, assets, liabilities, equity only).")
            except DataUnavailable as e:
                raise DataUnavailable(f"{yf_error} SEC EDGAR also failed: {e}") from e
        else:
            raise
    missing = [k for k in ("income_statement", "balance_sheet", "cash_flow") if k not in payload]
    if missing:
        notes.append("Not available from the source: " + ", ".join(m.replace("_", " ") for m in missing) + ".")
    result = CompanyData(payload, source, _now(), notes=notes)
    _write(symbol, "statements", result)
    return result
