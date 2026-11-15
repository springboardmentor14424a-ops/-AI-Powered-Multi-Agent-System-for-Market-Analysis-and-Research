from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from database.connection import get_db
from models.user import User, SavedStock
from schemas.auth import SavedStockCreate, SavedStockResponse

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("/", response_model=list[SavedStockResponse])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedStockResponse]:
    """Return all saved stocks for the current user."""
    result = await db.execute(
        select(SavedStock)
        .where(SavedStock.user_id == current_user.id)
        .order_by(SavedStock.added_at.desc())
    )
    stocks = result.scalars().all()
    return [SavedStockResponse.model_validate(s) for s in stocks]


@router.post("/", response_model=SavedStockResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: SavedStockCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedStockResponse:
    """Add a stock to the user's watchlist."""
    # Check for duplicate
    result = await db.execute(
        select(SavedStock).where(
            SavedStock.user_id == current_user.id,
            SavedStock.ticker == payload.ticker,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock is already in your watchlist.",
        )

    saved_stock = SavedStock(
        user_id=current_user.id,
        ticker=payload.ticker,
        company_name=payload.company_name,
        market=payload.market,
    )
    db.add(saved_stock)
    await db.flush()
    await db.refresh(saved_stock)
    return SavedStockResponse.model_validate(saved_stock)


@router.delete("/{saved_stock_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    saved_stock_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a stock from the user's watchlist."""
    result = await db.execute(
        select(SavedStock).where(SavedStock.id == saved_stock_id)
    )
    saved_stock: SavedStock | None = result.scalar_one_or_none()

    if saved_stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved stock not found.",
        )

    if saved_stock.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove this stock.",
        )

    await db.delete(saved_stock)
