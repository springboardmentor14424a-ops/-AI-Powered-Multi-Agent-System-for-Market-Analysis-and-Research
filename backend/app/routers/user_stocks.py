from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.user import User
from app.models.watchlist import Watchlist, RecentSearch
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistItem,
    RecentSearchCreate,
    RecentSearchItem,
)
from app.middleware.auth_middleware import get_current_user
from app.services.stock_service import get_stock_quote

router = APIRouter(prefix="/api/user", tags=["user-stocks"])


# --- Watchlist Endpoints ---

@router.get("/watchlist", response_model=List[WatchlistItem])
def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id)
        .order_by(desc(Watchlist.created_at))
        .all()
    )
    result = []
    for item in items:
        # Include quick quote info if available
        quote = get_stock_quote(item.symbol)
        price = quote.get("price") or quote.get("currentPrice")
        prev = quote.get("previous_close") or quote.get("previousClose")
        change = round(price - prev, 2) if price and prev else None
        change_pct = round((change / prev) * 100, 2) if change and prev else None

        result.append(
            WatchlistItem(
                id=item.id,
                symbol=item.symbol,
                name=item.name or quote.get("name", ""),
                created_at=item.created_at,
                price=price,
                change=change,
                changePercent=change_pct,
            )
        )
    return result


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    body: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sym = body.symbol.upper().strip()
    existing = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.symbol == sym)
        .first()
    )
    if existing:
        return {"message": "Already in watchlist", "item_id": existing.id}

    item = Watchlist(
        user_id=current_user.id,
        symbol=sym,
        name=body.name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Added to watchlist", "item_id": item.id}


@router.delete("/watchlist/{symbol}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(
    symbol: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sym = symbol.upper().strip()
    item = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == current_user.id, Watchlist.symbol == sym)
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found in watchlist",
        )
    db.delete(item)
    db.commit()
    return {"message": "Removed from watchlist"}


# --- Recent Searches Endpoints ---

@router.get("/recent-searches", response_model=List[RecentSearchItem])
def get_recent_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(RecentSearch)
        .filter(RecentSearch.user_id == current_user.id)
        .order_by(desc(RecentSearch.searched_at))
        .limit(10)
        .all()
    )
    return items


@router.post("/recent-searches", status_code=status.HTTP_200_OK)
def add_recent_search(
    body: RecentSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sym = body.symbol.upper().strip()
    existing = (
        db.query(RecentSearch)
        .filter(RecentSearch.user_id == current_user.id, RecentSearch.symbol == sym)
        .first()
    )
    if existing:
        existing.name = body.name or existing.name
        db.commit()
        db.refresh(existing)
        return {"message": "Updated recent search", "item_id": existing.id}

    item = RecentSearch(
        user_id=current_user.id,
        symbol=sym,
        name=body.name,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message": "Added recent search", "item_id": item.id}


@router.delete("/recent-searches", status_code=status.HTTP_200_OK)
def clear_recent_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(RecentSearch).filter(RecentSearch.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Recent searches cleared"}
