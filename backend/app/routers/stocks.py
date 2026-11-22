from fastapi import APIRouter, HTTPException, Query

from app.services.yahoo_finance import get_stock_history
from app.services.stock_search import search_stocks

router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"]
)


@router.get("/history")
def get_stock_history_api(
    ticker: str = Query(..., min_length=1),
    market: str = Query("NSE"),
    period: str = Query("1y")
):
    allowed_periods = ["1mo", "3mo", "6mo", "1y", "5y"]
    allowed_markets = ["NSE", "BSE", "NASDAQ", "NYSE"]

    # Validate the market
    market = market.strip().upper()

    if market not in allowed_markets:
        raise HTTPException(
            status_code=400,
            detail="Invalid market. Choose NSE, BSE, NASDAQ or NYSE."
        )

    # Validate the analysis period
    if period not in allowed_periods:
        raise HTTPException(
            status_code=400,
            detail="Invalid period. Choose 1mo, 3mo, 6mo, 1y or 5y."
        )

    ticker = ticker.strip().upper()

    # Normalise ticker symbol for Yahoo Finance
    if market == "NSE":
        if ticker.endswith(".BO"):
            ticker = ticker[:-3]
        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"

    elif market == "BSE":
        if ticker.endswith(".NS"):
            ticker = ticker[:-3]
        if not ticker.endswith(".BO"):
            ticker = ticker + ".BO"

    else:  # NASDAQ or NYSE
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            ticker = ticker[:-3]
        ticker = ticker.split(".")[0]

    # Retrieve historical OHLCV data directly via yfinance
    result = get_stock_history(ticker, period)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"]
        )

    result["market"] = market

    return result


@router.get("/search")
def search_stocks_api(
    query: str = Query(..., min_length=2)
):
    result = search_stocks(query.strip())

    if not result["success"]:
        raise HTTPException(
            status_code=502,
            detail=result["message"]
        )

    return result
