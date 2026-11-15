from fastapi import APIRouter, Depends, Query

from ..deps import get_current_user
from ..models import User
from ..schemas import Market, StockOut
from ..stock_service import search

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=list[StockOut])
def search_endpoint(
    q: str = Query(min_length=1, max_length=50),
    market: Market | None = None,
    _user: User = Depends(get_current_user),
):
    """Search companies by name or ticker symbol, optionally limited to one market."""
    return search(q, market)
