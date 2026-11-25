from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.preference import UserPreference
from app.models.stock import SavedStock
from app.api.auth import get_current_user
from app.services.market_data import (
    fetch_market_bundle,
    format_ticker_for_market,
    normalize_market,
    normalize_period,
    search_companies,
)

router = APIRouter(prefix="/api/workspace", tags=["Workspace"])


class PreferenceUpdate(BaseModel):
    preferred_market: str = Field(..., examples=["NSE", "BSE", "NASDAQ", "NYSE"])
    analysis_period: str = Field(..., examples=["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"])
    risk_tolerance: str = Field(default="Moderate")


class StockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)
    company_name: str | None = Field(default=None, max_length=150)
    market: str | None = Field(default=None, max_length=50)


def _get_or_create_preference(db: Session, user_id: int) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        pref = UserPreference(
            user_id=user_id,
            preferred_market="NASDAQ",
            analysis_period="1 Year",
            risk_tolerance="Moderate",
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get("/preferences")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = _get_or_create_preference(db, current_user.id)
    return {
        "preferred_market": pref.preferred_market,
        "analysis_period": pref.analysis_period,
        "risk_tolerance": pref.risk_tolerance,
    }


@router.put("/preferences")
def update_preferences(
    payload: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        valid_market = normalize_market(payload.preferred_market)
        valid_period_label, _ = normalize_period(payload.analysis_period)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    pref = _get_or_create_preference(db, current_user.id)
    pref.preferred_market = valid_market
    pref.analysis_period = valid_period_label
    pref.risk_tolerance = payload.risk_tolerance.strip() or "Moderate"

    db.commit()
    db.refresh(pref)
    return {
        "message": "Workspace preferences updated.",
        "preferred_market": pref.preferred_market,
        "analysis_period": pref.analysis_period,
        "risk_tolerance": pref.risk_tolerance,
    }


@router.get("/stocks/search")
def search_watchlist_stocks(
    q: str = Query(..., min_length=1),
    market: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = _get_or_create_preference(db, current_user.id)
    target_market = market or pref.preferred_market
    try:
        results = search_companies(query=q, market=target_market)
        return {"market": normalize_market(target_market), "results": results}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/stocks")
def list_saved_stocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stocks = (
        db.query(SavedStock)
        .filter(SavedStock.user_id == current_user.id)
        .order_by(SavedStock.created_at.desc())
        .all()
    )
    return {
        "stocks": [
            {
                "id": s.id,
                "ticker": s.ticker,
                "company_name": s.company_name,
                "market": s.market,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in stocks
        ]
    }


@router.post("/stocks", status_code=status.HTTP_201_CREATED)
def add_saved_stock(
    payload: StockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = _get_or_create_preference(db, current_user.id)
    target_market = payload.market or pref.preferred_market

    try:
        normalized_market = normalize_market(target_market)
        yf_symbol = format_ticker_for_market(payload.ticker, normalized_market)
        bundle = fetch_market_bundle(
            symbol=payload.ticker,
            market=normalized_market,
            period="1 Month",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to verify ticker with market provider: {exc}",
        ) from exc

    clean_ticker = bundle["ticker"]
    canonical_name = (
        payload.company_name.strip()
        if payload.company_name and payload.company_name.strip()
        else bundle["profile"]["company_name"]
    )

    existing = (
        db.query(SavedStock)
        .filter(
            SavedStock.user_id == current_user.id,
            SavedStock.ticker == clean_ticker,
            SavedStock.market == normalized_market,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{clean_ticker} ({normalized_market}) is already in your watchlist.",
        )

    stock = SavedStock(
        user_id=current_user.id,
        ticker=clean_ticker,
        company_name=canonical_name,
        market=normalized_market,
    )
    db.add(stock)
    db.commit()
    db.refresh(stock)

    return {
        "message": f"Added {canonical_name} ({yf_symbol}) to watchlist.",
        "stock": {
            "id": stock.id,
            "ticker": stock.ticker,
            "symbol": yf_symbol,
            "company_name": stock.company_name,
            "market": stock.market,
            "latest_close": bundle["summary_metrics"]["latest_close"],
            "source": bundle["source"],
            "retrieved_at": bundle["retrieved_at"],
            "created_at": stock.created_at.isoformat() if stock.created_at else None,
        },
    }


@router.delete("/stocks/{stock_id}")
def delete_saved_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = (
        db.query(SavedStock)
        .filter(SavedStock.id == stock_id, SavedStock.user_id == current_user.id)
        .first()
    )
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved stock not found.")

    db.delete(stock)
    db.commit()
    return {"message": f"Removed {stock.ticker} from watchlist."}