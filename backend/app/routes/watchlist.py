
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.models.saved_stock import SavedStock
from app.core.dependencies import get_current_user
from app.models.user import User

from app.services.stock_data_service import (
    validate_symbol,
    fetch_stock_data
)


router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)


# Add stock to watchlist
@router.post("/add")
def add_stock(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Step 1: Validate ticker format
    try:
        ticker = validate_symbol(ticker)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # Step 2: Check whether actual stock data exists
    try:
        stock_data = fetch_stock_data(
            ticker,
            period="1mo",
            interval="1d"
        )

        if stock_data is None or stock_data.empty:
            raise HTTPException(
                status_code=400,
                detail=f"No stock data available for {ticker}."
            )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker or no stock data found for {ticker}."
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Stock data provider is temporarily unavailable. Please try again."
        )

    # Step 3: Save valid stock to watchlist
    stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker
    )

    try:
        db.add(stock)
        db.commit()
        db.refresh(stock)

        return {
            "message": "Stock added successfully",
            "ticker": stock.ticker
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Stock already exists in your watchlist"
        )


# View logged-in user's watchlist
@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stocks = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id
    ).all()

    return stocks


# Remove stock from watchlist
@router.delete("/{saved_stock_id}")
def remove_stock(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stock = db.query(SavedStock).filter(
        SavedStock.saved_stock_id == saved_stock_id,
        SavedStock.user_id == current_user.user_id
    ).first()

    if stock is None:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in your watchlist"
        )

    db.delete(stock)
    db.commit()

    return {
        "message": "Stock removed successfully"
    }
