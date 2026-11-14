"""Company fundamentals.

US stocks   SEC EDGAR 'companyfacts' XBRL API (official filings)  -> Yahoo Finance
NSE / BSE   Yahoo Finance fundamentals

EDGAR needs SEC_USER_AGENT (your name + email) - the SEC asks every client to identify itself.
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import date

from ..config import settings
from ..stocks import provider_symbol
from . import DataUnavailable, data_dir

log = logging.getLogger(__name__)


@dataclass
class Fundamentals:
    metrics: dict
    source: str
    as_of: str | None = None
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- SEC EDGAR

_TAGS = {
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "assets": ["Assets"],
    "liabilities": ["Liabilities"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
}
_FLOW_ITEMS = {"revenue", "net_income"}  # measured over a period (vs. balance-sheet snapshots)


def _annual_series(facts: dict, tags: list[str], flow: bool) -> list[tuple[str, float]]:
    """[(period_end, value)] newest first, from 10-K full-year entries only. If several
    tags have data (companies switch tags over time) the one with the newest data wins."""
    usgaap = facts.get("facts", {}).get("us-gaap", {})
    best: list[tuple[str, float]] = []
    for tag in tags:
        entries = usgaap.get(tag, {}).get("units", {}).get("USD") or []
        by_end: dict[str, dict] = {}
        for e in entries:
            if e.get("fp") != "FY" or not str(e.get("form", "")).startswith("10-K"):
                continue
            if flow and e.get("start"):
                days = (date.fromisoformat(e["end"]) - date.fromisoformat(e["start"])).days
                if not 330 <= days <= 400:
                    continue
            prev = by_end.get(e["end"])
            if prev is None or e.get("filed", "") > prev.get("filed", ""):
                by_end[e["end"]] = e  # amended filings replace older ones
        series = sorted(((end, v["val"]) for end, v in by_end.items()), reverse=True)
        if series and (not best or series[0][0] > best[0][0]):
            best = series
    return best


def parse_companyfacts(facts: dict) -> Fundamentals:
    s = {name: _annual_series(facts, tags, name in _FLOW_ITEMS) for name, tags in _TAGS.items()}
    m: dict = {}
    as_of = None
    rev, ni = s["revenue"], s["net_income"]
    if rev:
        as_of = rev[0][0]
        m["revenue"] = rev[0][1]
        if len(rev) > 1 and rev[1][1]:
            m["revenue_growth"] = rev[0][1] / rev[1][1] - 1
    if ni:
        m["net_income"] = ni[0][1]
        if rev and ni[0][0] == rev[0][0] and rev[0][1]:
            m["net_margin"] = ni[0][1] / rev[0][1]
    assets, liab, eq = s["assets"], s["liabilities"], s["equity"]
    if assets:
        m["total_assets"] = assets[0][1]
    if liab:
        m["total_liabilities"] = liab[0][1]
        if assets and assets[0][1]:
            m["liabilities_to_assets"] = liab[0][1] / assets[0][1]
    if eq and ni and eq[0][1] and eq[0][1] > 0:
        m["roe"] = ni[0][1] / eq[0][1]
    if not m:
        raise DataUnavailable("EDGAR returned no usable annual figures")
    as_of = as_of or (assets[0][0] if assets else None)
    return Fundamentals(m, "SEC EDGAR company facts (10-K filings)", as_of)


def _cached_json(name: str, fetch, max_age_hours: float = 24):
    path = data_dir("cache", "sec", name)
    try:
        if path.exists() and (time.time() - path.stat().st_mtime) / 3600 < max_age_hours:
            return json.loads(path.read_text())
    except (OSError, ValueError):
        pass
    data = fetch()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    except OSError:
        pass
    return data


def _sec_get(url: str):
    import requests

    r = requests.get(
        url, headers={"User-Agent": settings.SEC_USER_AGENT}, timeout=settings.HTTP_TIMEOUT
    )
    r.raise_for_status()
    return r.json()


def get_edgar(ticker: str) -> Fundamentals:
    try:
        tickers = _cached_json("company_tickers.json", lambda: _sec_get("https://www.sec.gov/files/company_tickers.json"))
        cik = next((v["cik_str"] for v in tickers.values() if v["ticker"].upper() == ticker.upper()), None)
        if cik is None:
            raise DataUnavailable(f"{ticker} not found in the SEC company list")
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
        facts = _cached_json(f"facts_{int(cik):010d}.json", lambda: _sec_get(url))
    except DataUnavailable:
        raise
    except Exception as e:
        log.warning("SEC EDGAR request failed for %s: %s", ticker, e)
        raise DataUnavailable("SEC EDGAR could not be reached.") from e
    return parse_companyfacts(facts)


# ---------------------------------------------------------------- Yahoo Finance

_YF_FIELDS = {
    "trailing_pe": "trailingPE",
    "forward_pe": "forwardPE",
    "price_to_book": "priceToBook",
    "net_margin": "profitMargins",
    "revenue_growth": "revenueGrowth",
    "roe": "returnOnEquity",
    "market_cap": "marketCap",
}


def fetch_yf_fundamentals(symbol: str) -> Fundamentals:
    try:
        import yfinance as yf

        info = yf.Ticker(symbol).info
    except Exception as e:
        log.warning("Yahoo Finance fundamentals request failed for %s: %s", symbol, e)
        raise DataUnavailable(f"Could not download fundamentals for {symbol} from Yahoo Finance.") from e
    if not info or len(info) < 5:
        raise DataUnavailable(f"Yahoo Finance has no fundamentals for {symbol}")
    m = {k: info.get(src) for k, src in _YF_FIELDS.items()}
    de = info.get("debtToEquity")  # Yahoo reports this as a percentage (e.g. 145 = 1.45x)
    m["debt_to_equity"] = de / 100 if isinstance(de, (int, float)) else None
    m = {k: v for k, v in m.items() if isinstance(v, (int, float))}
    if not m:
        raise DataUnavailable(f"Yahoo Finance has no usable fundamentals for {symbol}")
    return Fundamentals(m, "Yahoo Finance fundamentals (yfinance)", None)


def get_fundamentals(market: str, ticker: str) -> Fundamentals:
    notes: list[str] = []
    if market in ("NASDAQ", "NYSE"):
        if settings.SEC_USER_AGENT:
            try:
                return get_edgar(ticker)
            except DataUnavailable as e:
                notes.append(f"EDGAR unavailable ({e}); used Yahoo Finance instead.")
        else:
            notes.append("SEC_USER_AGENT is not set, so SEC EDGAR was skipped; used Yahoo Finance fundamentals.")
    result = fetch_yf_fundamentals(provider_symbol(market, ticker))
    result.notes = notes + result.notes
    return result
