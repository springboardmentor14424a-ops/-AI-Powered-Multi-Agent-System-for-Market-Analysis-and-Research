"""Stock search/lookup backed by Yahoo Finance through the open-source `yfinance` library.

Everything here is best-effort: if yfinance is missing, Yahoo is unreachable or rate-limits us,
the functions return None and the caller falls back to the built-in ticker list
(see stock_service.py). Results are cached for a few minutes to avoid hammering Yahoo.
"""
import logging
import time

from .config import settings

logger = logging.getLogger(__name__)

# Yahoo exchange codes -> our market names (NSE/BSE are detected by the .NS/.BO suffix instead)
EXCHANGE_TO_MARKET = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NYQ": "NYSE"}

_CACHE: dict[tuple, tuple[float, list[dict]]] = {}
_CACHE_TTL_SECONDS = 600
_CACHE_MAX_ENTRIES = 300


def clear_cache() -> None:
    _CACHE.clear()


def _raw_quotes(query: str) -> list[dict]:
    """Call Yahoo's search endpoint. Isolated in one function so tests can replace it."""
    import yfinance as yf  # imported lazily so the app still starts if yfinance isn't installed

    try:
        result = yf.Search(query, max_results=20, news_count=0, timeout=6)
    except TypeError:  # older yfinance versions without these keyword arguments
        result = yf.Search(query, max_results=20)
    return list(result.quotes or [])


def _to_stock(quote: dict) -> dict | None:
    """Convert one Yahoo quote into our stock shape, or None if it isn't a supported listing."""
    if quote.get("quoteType") != "EQUITY":  # skip ETFs, funds, crypto, currencies...
        return None
    symbol = str(quote.get("symbol") or "").strip().upper()
    if not symbol:
        return None

    if symbol.endswith(".NS"):
        ticker, market = symbol[:-3], "NSE"
    elif symbol.endswith(".BO"):
        ticker, market = symbol[:-3], "BSE"
    elif "." in symbol:  # other foreign exchanges (.L, .TO, ...) are out of scope
        return None
    else:
        market = EXCHANGE_TO_MARKET.get(str(quote.get("exchange") or ""))
        ticker = symbol
        if market is None:
            return None

    if not ticker or len(ticker) > 20:
        return None
    name = str(quote.get("longname") or quote.get("shortname") or ticker).strip()
    return {
        "ticker": ticker,
        "name": name[:150],
        "market": market,
        "provider_symbol": symbol,
        "source": "yahoo",
    }


def _search_all_markets(query: str) -> list[dict] | None:
    """Cached Yahoo search, converted to our shape. None means Yahoo was unavailable."""
    key = query.strip().lower()
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < _CACHE_TTL_SECONDS:
        return hit[1]
    try:
        quotes = _raw_quotes(query.strip())
    except Exception as exc:  # ImportError, network errors, rate limiting, parse errors...
        logger.warning("Yahoo Finance search failed (%s); using built-in list", exc)
        return None

    stocks, seen = [], set()
    for q in quotes:
        stock = _to_stock(q) if isinstance(q, dict) else None
        if stock and (stock["ticker"], stock["market"]) not in seen:
            seen.add((stock["ticker"], stock["market"]))
            stocks.append(stock)

    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        _CACHE.clear()
    _CACHE[key] = (now, stocks)
    return stocks


def search_yahoo(query: str, market: str | None = None, limit: int = 10) -> list[dict] | None:
    """Search Yahoo by company name or ticker. None = unavailable (caller should fall back)."""
    if not settings.YAHOO_SEARCH_ENABLED or not query.strip():
        return None
    stocks = _search_all_markets(query)
    if stocks is None:
        return None
    if market:
        stocks = [s for s in stocks if s["market"] == market]
    return stocks[:limit]


def lookup_yahoo(ticker: str, market: str) -> dict | None:
    """Confirm that `ticker` exists on `market` according to Yahoo. None if not found/unavailable."""
    stocks = search_yahoo(ticker, market, limit=20)
    ticker = ticker.strip().upper()
    for s in stocks or []:
        if s["ticker"] == ticker and s["market"] == market:
            return s
    return None
