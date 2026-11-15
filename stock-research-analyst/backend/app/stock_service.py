"""Single entry point for stock search/validation: Yahoo Finance first, built-in list as fallback."""
from .stock_catalog import find_stock, provider_symbol, search_stocks
from .yahoo_search import lookup_yahoo, search_yahoo


def search(query: str, market: str | None = None) -> list[dict]:
    results = search_yahoo(query, market)
    if results:
        return results
    # Yahoo disabled / unreachable / no matches -> built-in ticker list
    return [{**s, "source": "catalog"} for s in search_stocks(query, market)]


def resolve(ticker: str, market: str) -> dict | None:
    """Validate that a ticker exists on a market and return its details (None if unknown)."""
    known = find_stock(ticker, market)  # instant, no network
    if known:
        return {**known, "provider_symbol": provider_symbol(known["ticker"], market), "source": "catalog"}
    return lookup_yahoo(ticker, market)
