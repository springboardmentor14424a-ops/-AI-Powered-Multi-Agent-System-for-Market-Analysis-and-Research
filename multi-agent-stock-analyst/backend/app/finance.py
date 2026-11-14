import yfinance as yf

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user

router = APIRouter(
    prefix="/finance",
    tags=["Finance"]
)


@router.get("/stock/{ticker}")
def get_stock(
    ticker: str,
    current_user=Depends(get_current_user)
):

    try:
        stock = yf.Ticker(ticker)

        history = stock.history(period="1mo")

        if history.empty:
            raise HTTPException(
                status_code=404,
                detail="Stock data not found"
            )

        latest = history.iloc[-1]

        previous = (
            history.iloc[-2]
            if len(history) > 1
            else latest
        )

        price = float(latest["Close"])
        previous_close = float(previous["Close"])

        change = price - previous_close

        return {
            "ticker": ticker.upper(),
            "current_price": price,
            "previous_close": previous_close,
            "change": change,
            "change_percent": (
                change / previous_close * 100
                if previous_close else 0
            ),
            "day_high": float(latest["High"]),
            "day_low": float(latest["Low"])
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve stock data"
        )
@router.get("/history/{ticker}")
def get_stock_history(
    ticker: str,
    period: str = "1mo",
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
        stock = yf.Ticker(ticker)

        history = stock.history(
            period=period
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
            "ticker": ticker.upper(),
            "period": period,
            "history": result
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve historical data"
        )