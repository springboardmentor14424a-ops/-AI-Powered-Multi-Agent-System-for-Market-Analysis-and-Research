from fastapi import APIRouter, HTTPException, Query
from app.services.market_data import search_companies, fetch_market_bundle

router = APIRouter(prefix="/api/market", tags=["Market Data"])


@router.get("/search")
def market_search(
    q: str = Query(..., min_length=1, description="Company name or ticker symbol"),
    market: str | None = Query(default=None, description="NSE, BSE, NASDAQ, or NYSE"),
):
    try:
        results = search_companies(query=q, market=market)
        return {"results": results}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/quote")
def market_quote(
    symbol: str = Query(..., min_length=1),
    market: str = Query(default="NASDAQ"),
    period: str = Query(default="1 Year"),
):
    try:
        return fetch_market_bundle(symbol=symbol, market=market, period=period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc