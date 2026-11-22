
"""
company.py – FastAPI router
===========================
Endpoints:
  GET /company/profile      – Company profile
  GET /company/financials   – Financial statements (income / balance_sheet / cashflow)

Both endpoints are public (no JWT required) so the Research page can call them
without an extra auth header on the same session. Sensitive DB operations still
require auth through their own routers.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Literal

from app.services.company_data import (
    get_company_profile,
    get_financial_statements,
)

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)

ALLOWED_MARKETS = ("NSE", "BSE", "NASDAQ", "NYSE")
ALLOWED_STATEMENTS = ("income", "balance_sheet", "cashflow")
ALLOWED_FREQUENCIES = ("annual", "quarterly")


@router.get("/profile")
def company_profile_api(
    ticker: str = Query(..., min_length=1, description="Stock ticker symbol"),
    market: str = Query("NSE", description="Exchange: NSE, BSE, NASDAQ or NYSE"),
):
    """
    Retrieve a company's profile including name, sector, industry, description,
    market cap, website, key financial ratios, and more.

    Returns a retrieval timestamp and data source for auditability.
    """
    market = market.strip().upper()

    if market not in ALLOWED_MARKETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market '{market}'. Choose NSE, BSE, NASDAQ or NYSE.",
        )

    result = get_company_profile(ticker.strip(), market)

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"],
        )

    return result


@router.get("/financials")
def company_financials_api(
    ticker: str = Query(..., min_length=1, description="Stock ticker symbol"),
    market: str = Query("NSE", description="Exchange: NSE, BSE, NASDAQ or NYSE"),
    statement: str = Query(
        "income",
        description="Statement type: income | balance_sheet | cashflow",
    ),
    frequency: str = Query(
        "annual",
        description="Reporting frequency: annual | quarterly",
    ),
):
    """
    Retrieve a financial statement for a company.

    - statement: 'income' | 'balance_sheet' | 'cashflow'
    - frequency: 'annual' | 'quarterly'

    Returns the full statement as a dict keyed by reporting date (YYYY-MM-DD),
    with each line item as a key and its numeric value (or null) as the value.

    Also returns:
    - reporting_periods : list of available dates, newest first
    - validation_warnings : list of data quality issues detected
    - retrieved_at : UTC timestamp of retrieval
    - data_source : provider name
    """
    market = market.strip().upper()
    statement = statement.strip().lower()
    frequency = frequency.strip().lower()

    if market not in ALLOWED_MARKETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market '{market}'. Choose NSE, BSE, NASDAQ or NYSE.",
        )

    if statement not in ALLOWED_STATEMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid statement '{statement}'. "
                   f"Choose from: {', '.join(ALLOWED_STATEMENTS)}",
        )

    if frequency not in ALLOWED_FREQUENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid frequency '{frequency}'. "
                   f"Choose 'annual' or 'quarterly'.",
        )

    result = get_financial_statements(
        ticker.strip(), market, statement, frequency  # type: ignore[arg-type]
    )

    if not result["success"]:
        raise HTTPException(
            status_code=404,
            detail=result["message"],
        )

    return result
