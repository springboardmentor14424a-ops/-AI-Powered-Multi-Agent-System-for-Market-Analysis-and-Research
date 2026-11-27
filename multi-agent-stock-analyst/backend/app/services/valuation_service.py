import time
from datetime import datetime, timezone
import yfinance as yf

_CACHE = {}          # key -> (timestamp, value)
_TTL = 600           # 10 minutes, avoids Yahoo rate limits


def _cached(key):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < _TTL:
        return hit[1]
    return None


def _store(key, value):
    _CACHE[key] = (time.time(), value)
    return value


def _clean_name(name: str) -> str:
    n = name.strip()
    for suffix in (" LTD.", " LTD", " LIMITED", " PVT", " PRIVATE"):
        if n.upper().endswith(suffix):
            n = n[: -len(suffix)]
    return n.strip()


def resolve_ticker(query: str):
    """Return (symbol, display_name) or None. Prefers NSE, then BSE."""
    key = ("ticker", query.lower())
    cached = _cached(key)
    if cached is not None:
        return cached or None

    for q in (query, _clean_name(query)):
        try:
            quotes = yf.Search(q, max_results=10).quotes
        except Exception:
            continue
        equities = [x for x in quotes if x.get("quoteType") == "EQUITY"]
        for suffix in (".NS", ".BO"):
            for x in equities:
                if x.get("symbol", "").endswith(suffix):
                    return _store(key, (x["symbol"], x.get("longname") or x.get("shortname")))
        if equities:
            x = equities[0]
            return _store(key, (x["symbol"], x.get("longname") or x.get("shortname")))
    _store(key, ())
    return None


def _num(v):
    try:
        return None if v is None else round(float(v), 2)
    except (TypeError, ValueError):
        return None


def get_valuation(query: str):
    resolved = resolve_ticker(query)
    if not resolved:
        raise ValueError(f"Could not find a Yahoo Finance ticker for '{query}'.")
    symbol, name = resolved

    key = ("val", symbol)
    cached = _cached(key)
    if cached:
        return cached

    info = yf.Ticker(symbol).info or {}
    roe = info.get("returnOnEquity")          # Yahoo returns a fraction (0.21)

    return _store(key, {
        "company": info.get("longName") or name or query,
        "ticker": symbol,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "currency": info.get("currency"),
        "pe_ratio": _num(info.get("trailingPE")),
        "pb_ratio": _num(info.get("priceToBook")),
        "roe_percent": _num(roe * 100) if roe is not None else None,
        "source": "Yahoo Finance",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    })