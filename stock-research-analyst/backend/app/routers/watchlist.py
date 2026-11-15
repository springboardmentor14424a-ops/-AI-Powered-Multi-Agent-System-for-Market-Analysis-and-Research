from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User
from ..schemas import SavedStockOut, WatchlistAdd
from ..stock_service import resolve

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[SavedStockOut])
def list_saved(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(SavedStock).where(SavedStock.user_id == user.user_id).order_by(SavedStock.created_at.desc())
    return db.scalars(stmt).all()


@router.post("", response_model=SavedStockOut, status_code=status.HTTP_201_CREATED)
def add_saved(payload: WatchlistAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stock = resolve(payload.ticker, payload.market)
    if stock is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Unknown ticker for the selected market.")

    exists = db.scalar(
        select(SavedStock).where(SavedStock.user_id == user.user_id, SavedStock.ticker == stock["ticker"])
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"{stock['ticker']} is already in your watchlist.")

    item = SavedStock(
        user_id=user.user_id,  # from the verified JWT, never from the request body
        ticker=stock["ticker"],
        company_name=stock["name"],
        market=stock["market"],
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:  # unique (user_id, ticker) constraint as a safety net
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"{stock['ticker']} is already in your watchlist.")
    db.refresh(item)
    return item


@router.delete("/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved(saved_stock_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.scalar(
        select(SavedStock).where(SavedStock.saved_stock_id == saved_stock_id, SavedStock.user_id == user.user_id)
    )
    if item is None:  # also returned for other users' records, so ids can't be probed
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Saved stock not found.")
    db.delete(item)
    db.commit()
