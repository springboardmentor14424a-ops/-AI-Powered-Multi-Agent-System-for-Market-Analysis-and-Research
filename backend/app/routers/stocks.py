from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import SavedStock, User
from ..schemas import Market, StockOut, WatchlistIn, WatchlistOut
from ..stocks import find_stock, search_stocks

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/stocks/search", response_model=list[StockOut])
def search(
    q: str = Query(min_length=1, max_length=50),
    market: Market | None = None,
    user: User = Depends(get_current_user),
):
    """Search the validated ticker list by company name or ticker."""
    return search_stocks(q, market)


@router.get("/watchlist", response_model=list[WatchlistOut])
def list_watchlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the logged-in user's saved stocks."""
    stmt = (
        select(SavedStock)
        .where(SavedStock.user_id == user.id)
        .order_by(SavedStock.created_at.desc(), SavedStock.id.desc())
    )
    return db.scalars(stmt).all()


@router.post("/watchlist", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    stock = find_stock(payload.market, payload.ticker)
    if stock is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "That stock isn't in the supported list for this market."
        )

    exists = db.scalar(
        select(SavedStock.id).where(
            SavedStock.user_id == user.id,
            SavedStock.market == stock["market"],
            SavedStock.ticker == stock["ticker"],
        )
    )
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already in your watchlist.")

    saved = SavedStock(
        user_id=user.id,  # from the verified JWT, never from the request
        ticker=stock["ticker"],
        company_name=stock["company_name"],
        market=stock["market"],
    )
    db.add(saved)
    try:
        db.commit()
    except IntegrityError:  # double-click / simultaneous requests: the DB constraint wins
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Already in your watchlist.")
    return saved


@router.delete("/watchlist/{saved_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    saved_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    saved = db.scalar(
        select(SavedStock).where(SavedStock.id == saved_id, SavedStock.user_id == user.id)
    )
    if saved is None:  # someone else's entry looks exactly like a missing one
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved stock not found.")
    db.delete(saved)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
