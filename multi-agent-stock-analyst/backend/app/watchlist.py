from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Watchlist

router = APIRouter(
    prefix="/watchlist",
    tags=["Watchlist"]
)


class WatchlistRequest(BaseModel):
    ticker: str


# 1. Add a stock
@router.post("/add")
def add_stock(
    request: WatchlistRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=400,
            detail="Ticker cannot be empty"
        )

    existing = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.user_id,
        Watchlist.ticker == ticker
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Stock already exists in your watchlist"
        )

    new_stock = Watchlist(
        user_id=current_user.user_id,
        ticker=ticker
    )

    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)

    return {
        "message": "Stock added successfully",
        "id": new_stock.id,
        "ticker": new_stock.ticker
    }


# 2. Get the logged-in user's watchlist
@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    stocks = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.user_id
    ).order_by(Watchlist.created_at.desc()).all()

    return [
        {
            "id": stock.id,
            "ticker": stock.ticker,
            "created_at": stock.created_at
        }
        for stock in stocks
    ]


# 3. Remove a stock

# 3. Remove a stock
@router.delete("/{stock_id}")
def remove_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    stock = db.query(Watchlist).filter(
        Watchlist.id == stock_id,
        Watchlist.user_id == current_user.user_id
    ).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in your watchlist"
        )

    db.delete(stock)
    db.commit()

    return {
        "message": "Stock removed successfully"
    }
