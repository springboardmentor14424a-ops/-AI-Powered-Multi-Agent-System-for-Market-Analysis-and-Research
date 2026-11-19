
import yfinance as yf
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, Query
from app.auth import get_current_user
from app.market_utils import resolve_ticker
from datetime import datetime, timezone
import numpy as np

router = APIRouter(
    prefix="/finance",
    tags=["Finance"]
)
def make_json_safe(value):
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None

    if isinstance(value, np.integer):
        return int(value)

    return value

# --------------------------------------------------
# 1. STOCK OVERVIEW
# --------------------------------------------------


@router.get("/stock/{ticker}")
def get_stock(
    ticker: str,
    market: str = Query("NSE"),
    current_user=Depends(get_current_user)
):
    try:
        yahoo_ticker = resolve_ticker(ticker, market)

        stock = yf.Ticker(yahoo_ticker)

        history = stock.history(period="1mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="Stock data not found"
            )

        # Remove infinite values and records with missing OHLC prices
        history = history.replace(
            [np.inf, -np.inf],
            np.nan
        )

        history = history.dropna(
            subset=["Open", "High", "Low", "Close"]
        )

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="No valid stock price records available"
            )

        # Get the latest valid records
        latest = history.iloc[-1]

        previous = (
            history.iloc[-2]
            if len(history) > 1
            else latest
        )

        price = float(latest["Close"])
        previous_close = float(previous["Close"])

        # Calculate price changes
        change = price - previous_close

        change_percent = (
            change / previous_close * 100
            if previous_close != 0
            else 0.0
        )

        # Verify all calculated values are finite
        values = [
            price,
            previous_close,
            change,
            change_percent,
            float(latest["High"]),
            float(latest["Low"])
        ]

        if not all(np.isfinite(value) for value in values):
            raise HTTPException(
                status_code=500,
                detail="Invalid numerical values in stock data"
            )

        return {
            "ticker": yahoo_ticker,
            "current_price": price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": change_percent,
            "day_high": float(latest["High"]),
            "day_low": float(latest["Low"])
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Stock retrieval error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve stock data"
        )



# --------------------------------------------------
# 2. HISTORICAL STOCK DATA
# --------------------------------------------------

@router.get("/history/{ticker}")
def get_stock_history(
    ticker: str,
    period: str = "1mo",
    market: str = Query("NSE"),
    current_user=Depends(get_current_user)
):
    allowed_periods = [
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "5y"
    ]

    if period not in allowed_periods:
        raise HTTPException(
            status_code=400,
            detail="Invalid analysis period"
        )

    try:
        yahoo_ticker = resolve_ticker(ticker, market)

        stock = yf.Ticker(yahoo_ticker)

        history = stock.history(period=period)
        history = history.replace(
            [np.inf, -np.inf],
            np.nan
        )
        history = history.dropna(
            subset=["Open", "High", "Low", "Close", "Volume"]
        )

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="Historical data not found"
            )

        result = []

        for date, row in history.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })

        return {
            "ticker": yahoo_ticker,
            "period": period,
            "history": result
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Historical data error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve historical data"
        )


# --------------------------------------------------
# 3. COMPANY PROFILE
# --------------------------------------------------

@router.get("/company/{ticker}/profile")
def get_company_profile(
    ticker: str,
    market: str = Query("NSE"),
    current_user=Depends(get_current_user)
):
    try:
        yahoo_ticker = resolve_ticker(ticker, market)

        stock = yf.Ticker(yahoo_ticker)

        info = stock.info

        if not info or not info.get("symbol"):
            raise HTTPException(
                status_code=404,
                detail="Company profile not found"
            )

        profile = {
            "company_name": info.get("longName"),
            "ticker": info.get("symbol"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "website": info.get("website"),
            "business_summary": info.get("longBusinessSummary"),
            "market_cap": info.get("marketCap"),
            "employees": info.get("fullTimeEmployees"),
            "exchange": info.get("exchange"),
            "currency": info.get("currency")
        }
        profile = make_json_safe(profile)

        return {
            "ticker": yahoo_ticker,
            "source": "Yahoo Finance",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Company profile error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve company profile"
        )


# --------------------------------------------------
# 4. COMPANY FINANCIAL STATEMENTS
# --------------------------------------------------

@router.get("/company/{ticker}/financials")
def get_company_financials(
    ticker: str,
    period: str = "annual",
    market: str = Query("NSE"),
    current_user=Depends(get_current_user)
):
    if period not in ["annual", "quarterly"]:
        raise HTTPException(
            status_code=400,
            detail="Period must be annual or quarterly"
        )

    try:
        yahoo_ticker = resolve_ticker(ticker, market)

        stock = yf.Ticker(yahoo_ticker)

        if period == "annual":
            income = stock.income_stmt
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow

        else:
            income = stock.quarterly_income_stmt
            balance_sheet = stock.quarterly_balance_sheet
            cash_flow = stock.quarterly_cashflow

        def convert_statement(statement):

            if statement.empty:
                return {}

            result = {}

            for date, column in statement.items():

                result[str(date.date())] = {
                    str(metric): (
                       float(value)
                       if pd.notna(value) and np.isfinite(float(value))
                       else None
                    )
                    for metric, value in column.items()
                }

            return result

        financial_data = {
            "income_statement": convert_statement(income),
            "balance_sheet": convert_statement(balance_sheet),
            "cash_flow_statement": convert_statement(cash_flow)
        }

        if not any(financial_data.values()):
            raise HTTPException(
                status_code=404,
                detail="Financial statements not available"
            )

        return {
            "ticker": yahoo_ticker,
            "period": period,
            "source": "Yahoo Finance",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "financial_statements": financial_data
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Financial statements error:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve financial statements"
        )
