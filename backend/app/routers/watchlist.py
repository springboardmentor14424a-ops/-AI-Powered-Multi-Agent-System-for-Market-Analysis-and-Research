
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.watchlist import Watchlist
from app.models.user import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    company_name: str,
    ticker: str,
    market: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_stock = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.user_id,
        Watchlist.ticker == ticker,
        Watchlist.market == market
    ).first()

    if existing_stock:
        raise HTTPException(
            status_code=400,
            detail="Stock already exists in your watchlist"
        )

    stock = Watchlist(
        user_id=current_user.user_id,
        company_name=company_name,
        ticker=ticker,
        market=market.upper()
    )

    db.add(stock)
    db.commit()
    db.refresh(stock)

    return {
        "message": "Stock added to watchlist",
        "watchlist_id": str(stock.watchlist_id),
        "company_name": stock.company_name,
        "ticker": stock.ticker,
        "market": stock.market
    }


@router.get("/")
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stocks = db.query(Watchlist).filter(
        Watchlist.user_id == current_user.user_id
    ).all()

    return stocks


@router.delete("/{watchlist_id}")
def remove_from_watchlist(
    watchlist_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stock = db.query(Watchlist).filter(
        Watchlist.watchlist_id == watchlist_id,
        Watchlist.user_id == current_user.user_id
    ).first()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in your watchlist"
        )

    db.delete(stock)
    db.commit()

    return {"message": "Stock removed from watchlist"}
