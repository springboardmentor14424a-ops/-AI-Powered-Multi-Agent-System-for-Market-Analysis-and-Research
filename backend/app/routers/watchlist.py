from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, SavedStock
from app.schemas import SavedStockCreate, SavedStockResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[SavedStockResponse])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all saved stocks in the logged-in user's watchlist.
    User ID derived strictly from JWT.
    """
    stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )
    return stocks

@router.post("", response_model=SavedStockResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    stock_in: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a stock ticker to the user's watchlist.
    Prevents duplicate ticker entries for the same user.
    """
    ticker_clean = stock_in.ticker.strip().upper()
    
    # Check for existing duplicate
    existing = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == ticker_clean
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticker '{ticker_clean}' is already in your watchlist."
        )

    saved_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker_clean
    )
    db.add(saved_stock)
    db.commit()
    db.refresh(saved_stock)
    return saved_stock

@router.delete("/{ticker}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(
    ticker: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a stock ticker from the user's watchlist.
    """
    ticker_clean = ticker.strip().upper()
    saved_stock = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.user_id,
            SavedStock.ticker == ticker_clean
        )
        .first()
    )
    if not saved_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticker '{ticker_clean}' not found in your watchlist."
        )

    db.delete(saved_stock)
    db.commit()
    return {"message": f"Ticker '{ticker_clean}' successfully removed from watchlist.", "ticker": ticker_clean}

