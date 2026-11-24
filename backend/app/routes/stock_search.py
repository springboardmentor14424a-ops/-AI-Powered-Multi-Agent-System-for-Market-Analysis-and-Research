
from fastapi import APIRouter, HTTPException, Query
import yfinance as yf


router = APIRouter(
    prefix="/api/stocks",
    tags=["Stock Search"]
)


# Yahoo Finance exchange codes -> StockPilot supported markets
EXCHANGE_MARKET_MAP = {
    # India
    "NSI": "NSE",
    "NSE": "NSE",
    "BSE": "BSE",

    # United States
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NCM": "NASDAQ",
    "NASDAQ": "NASDAQ",
    "NAS": "NASDAQ",

    "NYQ": "NYSE",
    "NYE": "NYSE",
    "NYSE": "NYSE",
}


def get_stock_market(symbol: str, exchange: str | None) -> str | None:
    """
    Identify the canonical StockPilot market.

    Prefer Yahoo Finance's exchange code.
    Use the ticker suffix as a fallback for Indian stocks.
    Return None when the market cannot be identified safely.
    """

    normalized_exchange = (exchange or "").strip().upper()

    market = EXCHANGE_MARKET_MAP.get(normalized_exchange)

    if market:
        return market

    normalized_symbol = (symbol or "").strip().upper()

    if normalized_symbol.endswith(".NS"):
        return "NSE"

    if normalized_symbol.endswith(".BO"):
        return "BSE"

    return None


@router.get("/search")
def search_stocks(
    query: str = Query(min_length=1, max_length=100)
):
    search_query = query.strip()

    if not search_query:
        raise HTTPException(
            status_code=400,
            detail="Please enter a company name or ticker"
        )

    try:
        search = yf.Search(
            search_query,
            max_results=10
        )

        results = []

        for item in search.quotes:
            if item.get("quoteType") != "EQUITY":
                continue

            ticker = item.get("symbol")

            if not ticker:
                continue

            company_name = (
                item.get("longname")
                or item.get("shortname")
                or ticker
            )

            exchange = item.get("exchange")

            market = get_stock_market(
                ticker,
                exchange
            )

            results.append({
                "ticker": ticker,
                "company_name": company_name,
                "exchange": exchange,
                "market": market,
                "type": item.get("quoteType")
            })

        return {
            "query": search_query,
            "results": results
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Stock search is temporarily unavailable. Please try again."
        )
