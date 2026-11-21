"""Live company search (Yahoo Finance) to go beyond the built-in ticker list."""
import logging

from ..stocks import provider_symbol

log = logging.getLogger(__name__)

_US_EXCHANGES = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NASDAQ": "NASDAQ",
                 "NYQ": "NYSE", "NYSE": "NYSE"}


def quote_to_stock(q: dict) -> dict | None:
    """Convert one Yahoo search hit into our {ticker, company_name, market} shape, or None
    when it is not an equity on a market we support."""
    if (q.get("quoteType") or "EQUITY").upper() != "EQUITY":
        return None
    symbol = str(q.get("symbol") or "").upper()
    name = q.get("longname") or q.get("shortname")
    if not symbol or not name:
        return None
    if symbol.endswith(".NS"):
        market, ticker = "NSE", symbol[:-3]
    elif symbol.endswith(".BO"):
        market, ticker = "BSE", symbol[:-3]
    else:
        market = _US_EXCHANGES.get(str(q.get("exchange") or "").upper())
        ticker = symbol
        if market is None or "." in symbol:
            return None
    return {"ticker": ticker, "company_name": name, "market": market,
            "provider_symbol": provider_symbol(market, ticker)}


def live_search(query: str, market: str | None = None, limit: int = 10) -> list[dict]:
    """Best effort: returns [] on any network/provider problem."""
    try:
        import yfinance as yf

        quotes = yf.Search(query, max_results=limit * 2, news_count=0).quotes
    except Exception as e:
        log.info("Live stock search failed: %s", e)
        return []
    out = []
    for q in quotes or []:
        stock = quote_to_stock(q)
        if stock and (market is None or stock["market"] == market):
            out.append(stock)
    return out[:limit]
