
from fastapi import APIRouter, HTTPException, Query, status

from app.services.market_data import (
    get_stock_profile,
    get_stock_history as fetch_stock_history,
    get_stock_financial_statements,
    MarketDataError
)

from app.schemas import (
    StockProfileResponse,
    StockHistoryResponse,
    StockFinancialStatementsResponse
)


router = APIRouter(
    prefix="/api/stocks",
    tags=["Stock Market Data"]
)


# --------------------------------------------------
# GET COMPANY PROFILE
# --------------------------------------------------

@router.get(
    "/{ticker}/profile",
    response_model=StockProfileResponse
)
def get_company_profile(
    ticker: str,
    market: str = Query(
        ...,
        min_length=1,
        max_length=30
    )
):
    ticker = ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid stock ticker"
        )

    try:
        return get_stock_profile(
            ticker=ticker,
            market=market
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    except MarketDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        )


# --------------------------------------------------
# GET HISTORICAL STOCK DATA (OHLCV)
# --------------------------------------------------

@router.get(
    "/{ticker}/history",
    response_model=StockHistoryResponse
)
def get_stock_history_endpoint(
    ticker: str,
    market: str = Query(
        ...,
        min_length=1,
        max_length=30
    ),
    period: str = Query(
        ...,
        min_length=1,
        max_length=10
    )
):
    ticker = ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid stock ticker"
        )

    try:
        return fetch_stock_history(
            ticker=ticker,
            market=market,
            period=period
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    except MarketDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        )


# --------------------------------------------------
# GET FINANCIAL STATEMENTS
# --------------------------------------------------

@router.get(
    "/{ticker}/financials",
    response_model=StockFinancialStatementsResponse
)
def get_stock_financial_statements_endpoint(
    ticker: str,
    market: str = Query(
        ...,
        min_length=1,
        max_length=30
    )
):
    ticker = ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid stock ticker"
        )

    try:
        return get_stock_financial_statements(
            ticker=ticker,
            market=market
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    except MarketDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        )
