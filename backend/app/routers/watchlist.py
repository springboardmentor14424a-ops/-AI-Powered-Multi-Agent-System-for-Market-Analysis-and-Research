from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User, UserPreference
from ..schemas import SavedStockCreate, SavedStockOut
from ..services import market_data
from ..services.market_data import NoDataError, ProviderError

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def verify_ticker(ticker: str, preferred_market: str) -> None:
    markets = [preferred_market]
    if preferred_market not in ("NASDAQ", "NYSE"):
        markets.append("NASDAQ")
    for market in markets:
        try:
            market_data.fetch_history(ticker, market, "1M")
            return
        except NoDataError:
            continue
        except ProviderError:
            raise HTTPException(
                status_code=502,
                detail="Could not verify the ticker with Yahoo Finance right now. Please try again.",
            )
    raise HTTPException(
        status_code=404,
        detail=f"Ticker {ticker} was not found. Check the symbol, or change your market in Preferences.",
    )


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

    pref = db.get(UserPreference, current_user.user_id)
    verify_ticker(data.ticker, pref.market if pref else "NSE")

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