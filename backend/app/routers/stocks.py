from fastapi import APIRouter, Query
from app.services.stock_service import search_stocks, get_stock_history, get_stock_quote

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/search")
def search(q: str = Query(..., description="Search query for stocks")):
    results = search_stocks(q)
    return results


@router.get("/{symbol}/history")
def history(symbol: str, period: str = "1y", interval: str = "1d"):
    data = get_stock_history(symbol, period=period, interval=interval)
    return data


@router.get("/{symbol}/quote")
def quote(symbol: str):
    data = get_stock_quote(symbol)
    return data
