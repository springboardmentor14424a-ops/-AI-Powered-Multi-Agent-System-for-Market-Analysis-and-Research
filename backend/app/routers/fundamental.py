"""
fundamental.py – FastAPI router for Fundamental Agent
=====================================================
Endpoints:
  POST /api/fundamental/analyze - Analyze fundamentals for a target stock
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.security import get_current_user
from app.models.user import User
from app.schemas.fundamental import (
    FundamentalAnalysisRequest,
    FundamentalAnalysisResponse,
)
from app.services.fundamental_agent_service import analyze_company_fundamentals

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=FundamentalAnalysisResponse,
    summary="Analyze company fundamentals",
    description=(
        "Executes in-memory Fundamental Agent analysis across all 8 analytical features: "
        "Revenue & Earnings, Profitability, Debt & Stability, Financial Ratios, Historical Comparison, "
        "Peer Comparison, Data Quality Detection, and Profitability Classification."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Fundamental analysis completed successfully"},
        400: {"description": "Invalid ticker or input validation failure"},
        401: {"description": "Authentication required"},
        404: {"description": "Company profile or statements not found"},
        502: {"description": "External data provider failure"},
        500: {"description": "Internal server or calculation error"},
    },
)
def analyze_stock_fundamentals(
    request: FundamentalAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Protected endpoint to analyze fundamentals for a given ticker and market.
    Requires authentication via Bearer JWT token.
    """
    clean_ticker = request.ticker.strip().upper()
    clean_market = request.market.strip().upper()

    try:
        # Call the existing Fundamental Agent service
        result = analyze_company_fundamentals(
            ticker=clean_ticker,
            market=clean_market,
        )
    except Exception as exc:
        logger.error(
            f"Unexpected exception analyzing fundamentals for {clean_ticker}:{clean_market}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "agent_name": "Fundamental Agent",
                "ticker": clean_ticker,
                "market": clean_market,
                "error": "An unexpected error occurred while analyzing fundamentals. Please try again later.",
            },
        )

    # Inspect service-level outcome
    if not result.get("success"):
        err_msg = result.get("error", "Fundamental analysis failed")
        err_lower = err_msg.lower()

        # Distinguish between 404 (not found / invalid symbol),
        # 502 (external data provider failure),
        # and 500 (calculation error)
        if "not found" in err_lower or "404" in err_lower or "no data found" in err_lower:
            status_code = status.HTTP_404_NOT_FOUND
        elif "failed to retrieve" in err_lower or "unavailable" in err_lower or "timeout" in err_lower:
            status_code = status.HTTP_502_BAD_GATEWAY
        elif "calculation error" in err_lower:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        return JSONResponse(
            status_code=status_code,
            content=result,
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=result,
    )
