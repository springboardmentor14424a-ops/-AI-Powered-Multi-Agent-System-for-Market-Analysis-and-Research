
import math

import yfinance as yf

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, SavedStock
from app.schemas import SavedStockCreate, SavedStockResponse


router = APIRouter(
    prefix="/api/watchlist",
    tags=["Watchlist"]
)


# Fetch the latest available price and daily percentage change
def get_stock_price(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        fast_info = stock.fast_info

        current_price = fast_info["last_price"]
        previous_close = fast_info["previous_close"]

        current_price = float(current_price)
        previous_close = float(previous_close)

        if (
            not math.isfinite(current_price)
            or not math.isfinite(previous_close)
            or previous_close == 0
        ):
            return None, None

        daily_change_percent = (
            (current_price - previous_close) / previous_close
        ) * 100

        return current_price, round(daily_change_percent, 2)

    except Exception:
        # Fallback: use the latest available daily history
        try:
            history = yf.Ticker(ticker).history(period="5d")

            if history.empty or len(history) < 2:
                return None, None

            current_price = float(history["Close"].iloc[-1])
            previous_close = float(history["Close"].iloc[-2])

            if previous_close == 0:
                return None, None

            daily_change_percent = (
                (current_price - previous_close) / previous_close
            ) * 100

            if not math.isfinite(current_price) or not math.isfinite(
                daily_change_percent
            ):
                return None, None

            return current_price, round(daily_change_percent, 2)

        except Exception:
            return None, None


# GET: View the logged-in user's watchlist with prices
@router.get("", response_model=list[SavedStockResponse])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )

    results = []

    for saved_stock in saved_stocks:
        current_price, daily_change_percent = get_stock_price(
            saved_stock.ticker
        )

        results.append({
            "saved_stock_id": saved_stock.saved_stock_id,
            "ticker": saved_stock.ticker,
            "created_at": saved_stock.created_at,
            "current_price": current_price,
            "daily_change_percent": daily_change_percent
        })

    return results


# POST: Add a stock to the watchlist
@router.post(
    "",
    response_model=SavedStockResponse,
    status_code=status.HTTP_201_CREATED
)
def add_to_watchlist(
    data: SavedStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticker = data.ticker.strip().upper()

    existing_stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == ticker
        )
        .first()
    )

    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stock is already in your watchlist"
        )

    saved_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker
    )

    db.add(saved_stock)
    db.commit()
    db.refresh(saved_stock)

    return saved_stock


# DELETE: Remove a stock from the watchlist
@router.delete("/{saved_stock_id}")
def remove_from_watchlist(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved_stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id
        )
        .first()
    )

    if not saved_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved stock not found"
        )

    db.delete(saved_stock)
    db.commit()

    return {
        "message": "Stock removed from watchlist successfully"
    }
