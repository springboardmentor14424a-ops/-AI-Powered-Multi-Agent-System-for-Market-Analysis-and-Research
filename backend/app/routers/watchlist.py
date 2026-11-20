from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User
from ..schemas import SavedStockCreate, SavedStockOut

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[SavedStockOut])
def list_saved(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )


@router.post("", response_model=SavedStockOut, status_code=status.HTTP_201_CREATED)
def add_saved(
    data: SavedStockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.user_id, SavedStock.ticker == data.ticker)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Already in your watchlist")

    item = SavedStock(user_id=current_user.user_id, ticker=data.ticker)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already in your watchlist")
    db.refresh(item)
    return item


@router.delete("/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved(
    saved_stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(SavedStock)
        .filter(
            SavedStock.saved_stock_id == saved_stock_id,
            SavedStock.user_id == current_user.user_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Saved stock not found")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)