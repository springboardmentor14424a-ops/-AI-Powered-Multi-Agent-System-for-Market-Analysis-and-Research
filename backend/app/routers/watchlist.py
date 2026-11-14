from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, SavedStock
from app.schemas import WatchlistItemResponse, WatchlistAddRequest
from app.dependencies import get_current_user
from app.services.market_data import (
    get_stock_quote,
    format_ticker_for_market,
    DEFAULT_TICKERS,
    search_companies_by_market
)

router = APIRouter(prefix="/api/watchlist", tags=["Saved Stocks & Watchlists"])

POPULAR_STOCKS = DEFAULT_TICKERS

@router.get("/companies")
def get_exchange_companies(
    market: str = Query(..., description="Exchange market: NSE, BSE, NASDAQ, NYSE"),
    q: Optional[str] = Query("", description="Company name or ticker prefix query")
):
    """
    Returns company suggestions strictly filtered by the selected exchange market.
    Matches companies based on prefix (case-insensitive) of company name or ticker.
    Never returns companies belonging to other exchanges.
    If no companies match, returns an empty list.
    """
    return search_companies_by_market(market, q or "")

@router.get("/quote/{ticker}")
def get_live_quote(ticker: str, market: Optional[str] = Query("NASDAQ")):
    """
    Fetches dynamic real-time market data from Yahoo Finance API for a specific ticker.
    """
    return get_stock_quote(ticker, market or "NASDAQ")

@router.get("/search")
def search_stocks(
    q: str = Query(..., min_length=1),
    market: Optional[str] = Query(None),
    strict: bool = Query(False)
):
    if strict and market:
        return search_companies_by_market(market, q)

    query = q.strip().upper()
    primary_matches = []
    other_matches = []

    for s in POPULAR_STOCKS:
        if query in s["ticker"] or query in s["name"].upper():
            if market and s["market"] == market:
                primary_matches.append(s)
            else:
                other_matches.append(s)

    # Preferred market first, then other available exchanges
    matches = primary_matches + other_matches

    # If no match or user typed a custom ticker, allow direct selection
    if not any(m["ticker"] == query for m in matches) and len(query) >= 1:
        matches.append({
            "ticker": query,
            "name": f"{query} Corporation",
            "market": market or "NASDAQ"
        })
    return matches

@router.get("", response_model=List[WatchlistItemResponse])
def get_user_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id
    ).order_by(SavedStock.created_at.desc()).all()

    # Enrich saved stocks with dynamic market data quotes
    results = []
    for s in saved:
        item = WatchlistItemResponse(
            saved_stock_id=s.saved_stock_id,
            ticker=s.ticker,
            company_name=s.company_name,
            market=s.market,
            created_at=s.created_at
        )
        try:
            q = get_stock_quote(s.ticker, s.market or "NASDAQ")
            item.last_price = q.get("last_price")
            item.change = q.get("change")
            item.change_pct = q.get("change_pct")
            item.currency = q.get("currency")
        except Exception:
            pass
        results.append(item)
    return results

@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    stock_in: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticker_clean = stock_in.ticker.strip().upper()

    # Prevent duplicate entries for the same user and ticker
    existing = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id,
        SavedStock.ticker == ticker_clean
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{ticker_clean} is already present in your watchlist."
        )

    company_name = stock_in.company_name
    market = stock_in.market
    if not company_name or not market:
        for item in POPULAR_STOCKS:
            if item["ticker"] == ticker_clean:
                company_name = company_name or item["name"]
                market = market or item["market"]
                break

    new_stock = SavedStock(
        user_id=current_user.user_id,
        ticker=ticker_clean,
        company_name=company_name or ticker_clean,
        market=market or "NASDAQ"
    )
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return new_stock

@router.delete("/{stock_identifier}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    stock_identifier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    identifier_clean = stock_identifier.strip().upper()
    stock = db.query(SavedStock).filter(
        SavedStock.user_id == current_user.user_id,
        (SavedStock.saved_stock_id == stock_identifier) | (SavedStock.ticker == identifier_clean)
    ).first()

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock was not found in your watchlist."
        )

    db.delete(stock)
    db.commit()
    return None
