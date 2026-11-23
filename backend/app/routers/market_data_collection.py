"""
Market Data Collection Router
Endpoints for Module 2:
- Company search across supported exchanges
- Data collection, OHLCV validation, and persistence
- Collections history and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, MarketDataCollection
from app.schemas import MarketDataCollectRequest, MarketDataCollectionSummary
from app.dependencies import get_current_user
from app.services.market_data_collection import (
    search_market_companies,
    fetch_market_data_collection,
    EXCHANGE_COMPANIES,
    VALID_INTERVALS
)

router = APIRouter(prefix="/api/market-data", tags=["Market Data Collection"])

@router.get("/search")
def search_companies(
    q: str = Query("", description="Company name or ticker symbol query"),
    market: str = Query("NASDAQ", description="Stock exchange: NSE, BSE, NASDAQ, or NYSE")
):
    """
    Search for companies within the specified stock exchange.
    Returns dynamic autocomplete suggestions containing ticker, name, market, and country.
    Strictly filters results to match the selected stock exchange.
    """
    market_upper = market.upper()
    if market_upper not in ["NSE", "BSE", "NASDAQ", "NYSE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported market '{market}'. Must be one of: NSE, BSE, NASDAQ, NYSE."
        )

    results = search_market_companies(market_upper, q)
    return results

@router.post("/collect", status_code=status.HTTP_201_CREATED)
def collect_market_data(
    payload: MarketDataCollectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Collects historical OHLCV data, validates data integrity, extracts company profile
    and real financial statements, records data source traceability and timestamps,
    and persists the validated dataset to PostgreSQL.
    """
    collected = fetch_market_data_collection(
        ticker=payload.ticker,
        market=payload.market,
        start_date=payload.start_date,
        end_date=payload.end_date,
        interval=payload.interval or "1d"
    )

    validation = collected.get("validation", {})
    val_status = validation.get("status", "PASSED")

    # Persist collection record in database
    db_collection = MarketDataCollection(
        user_id=current_user.user_id,
        ticker=collected["ticker"],
        company_name=collected["company_name"],
        market=collected["market"],
        country=collected["country"],
        start_date=collected["start_date"],
        end_date=collected["end_date"],
        interval=collected["interval"],
        data_source=collected["data_source"],
        retrieved_at=datetime.now(timezone.utc),
        record_count=collected["record_count"],
        validation_status=val_status,
        validation_summary=json.dumps(validation),
        ohlcv_data=json.dumps(collected["ohlcv_records"]),
        company_profile=json.dumps(collected["company_profile"]),
        financial_statements=json.dumps(collected["financial_statements"]),
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)

    return {
        "collection_id": db_collection.collection_id,
        **collected
    }

@router.get("/collections", response_model=List[MarketDataCollectionSummary])
def list_market_data_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all past collected market datasets for the authenticated user."""
    collections = db.query(MarketDataCollection).filter(
        MarketDataCollection.user_id == current_user.user_id
    ).order_by(MarketDataCollection.retrieved_at.desc()).all()
    return collections

@router.get("/collections/{collection_id}")
def get_market_data_collection_detail(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves detailed historical OHLCV records, company profile, and financial statements for a saved collection."""
    col = db.query(MarketDataCollection).filter(
        MarketDataCollection.collection_id == collection_id,
        MarketDataCollection.user_id == current_user.user_id
    ).first()

    if not col:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market data collection not found or unauthorized."
        )

    return {
        "collection_id": col.collection_id,
        "ticker": col.ticker,
        "company_name": col.company_name,
        "market": col.market,
        "country": col.country,
        "start_date": col.start_date,
        "end_date": col.end_date,
        "interval": col.interval,
        "data_source": col.data_source,
        "retrieved_at_utc": col.retrieved_at.isoformat(),
        "retrieved_at_local": col.retrieved_at.strftime("%Y-%m-%d %H:%M:%S"),
        "record_count": col.record_count,
        "validation": json.loads(col.validation_summary) if col.validation_summary else {},
        "ohlcv_records": json.loads(col.ohlcv_data) if col.ohlcv_data else [],
        "company_profile": json.loads(col.company_profile) if col.company_profile else {},
        "financial_statements": json.loads(col.financial_statements) if col.financial_statements else {}
    }

@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_market_data_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently deletes a saved market data collection."""
    col = db.query(MarketDataCollection).filter(
        MarketDataCollection.collection_id == collection_id,
        MarketDataCollection.user_id == current_user.user_id
    ).first()

    if not col:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market data collection not found."
        )

    db.delete(col)
    db.commit()
    return None
