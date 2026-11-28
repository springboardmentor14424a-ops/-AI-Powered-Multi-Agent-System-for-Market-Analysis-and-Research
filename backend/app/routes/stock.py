
import pandas as pd

from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from app.services.stock_data_service import (
    get_stock_analysis,
    search_companies,
    get_company_profile,
    get_financial_statements
)

from app.services.fundamental_analysis_service import (
    run_fundamental_analysis
)


router = APIRouter(
    prefix="/stocks",
    tags=["Stock Market"]
)


# ==========================================================
# HELPER: CONVERT PANDAS DATAFRAME INTO JSON RECORDS
# ==========================================================

def dataframe_to_records(data: pd.DataFrame) -> list:

    if data is None or data.empty:
        return []

    dataframe = data.copy()

    dataframe.index.name = dataframe.index.name or "Date"

    dataframe = dataframe.reset_index()

    records = []

    for record in dataframe.to_dict(orient="records"):

        clean_record = {}

        for key, value in record.items():

            if pd.isna(value):
                clean_record[key] = None

            elif isinstance(value, (pd.Timestamp, datetime, date)):
                clean_record[key] = value.isoformat()

            elif hasattr(value, "item"):
                clean_record[key] = value.item()

            else:
                clean_record[key] = value

        records.append(clean_record)

    return records


# ==========================================================
# 1. SEARCH COMPANIES
# ==========================================================

@router.get("/search")
def search_stock_companies(
    query: str = Query(min_length=1),
    market: str = Query(default="NSE"),
    max_results: int = Query(default=10, ge=1, le=25)
):

    try:

        results = search_companies(
            query=query,
            market=market,
            max_results=max_results
        )

        return {
            "query": query,
            "market": market.upper(),
            "source": "Yahoo Finance",
            "results_count": len(results),
            "results": results
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Company search failed: {str(error)}"
        )


# ==========================================================
# 2. FUNDAMENTAL ANALYSIS
# ==========================================================

@router.get("/{symbol}/fundamental-analysis")
def get_fundamental_analysis(symbol: str):

    try:

        result = run_fundamental_analysis(symbol)

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Fundamental analysis failed: {str(error)}"
        )


# ==========================================================
# 3. HISTORICAL STOCK ANALYSIS
# ==========================================================

@router.get("/{symbol}/analysis")
def get_analysis(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d")
):

    try:

        result = get_stock_analysis(
            symbol=symbol,
            period=period,
            interval=interval
        )

        historical_data = dataframe_to_records(
            result["historical_data"]
        )

        return {
            "symbol": result["symbol"],
            "period": result["period"],
            "interval": result["interval"],
            "summary": result["summary"],
            "historical_data": historical_data,
            "metadata": result.get("metadata", {})
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Stock analysis failed: {str(error)}"
        )


# ==========================================================
# 4. COMPANY PROFILE
# ==========================================================

@router.get("/{symbol}/profile")
def get_stock_profile(symbol: str):

    try:

        profile = get_company_profile(symbol)

        return profile

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Company profile retrieval failed: {str(error)}"
        )


# ==========================================================
# 5. FINANCIAL STATEMENTS
# ==========================================================

@router.get("/{symbol}/financials")
def get_stock_financials(symbol: str):

    try:

        result = get_financial_statements(symbol)

        return {
            "symbol": result["symbol"],

            "income_statement": dataframe_to_records(
                result["income_statement"]
            ),

            "balance_sheet": dataframe_to_records(
                result["balance_sheet"]
            ),

            "cash_flow": dataframe_to_records(
                result["cash_flow"]
            ),

            "metadata": result["metadata"]
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Financial statement retrieval failed: {str(error)}"
        )
