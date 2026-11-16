from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.preference import UserPreference
from app.models.stock import SavedStock
from app.core.security import get_current_user

router = APIRouter(prefix="/api/workspace", tags=["Workspace"])

class PreferenceUpdate(BaseModel):
    preferred_market: Optional[str] = "NSE"
    analysis_period: Optional[str] = "1 Year"
    risk_tolerance: Optional[str] = "Moderate"

class StockCreate(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = "NSE"

@router.get("/preferences")
def get_preferences(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id, preferred_market="NSE", analysis_period="1 Year", risk_tolerance="Moderate")
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@router.put("/preferences")
def update_preferences(payload: PreferenceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.id)
        db.add(prefs)
    
    if payload.preferred_market:
        prefs.preferred_market = payload.preferred_market
    if payload.analysis_period:
        prefs.analysis_period = payload.analysis_period
    if payload.risk_tolerance:
        prefs.risk_tolerance = payload.risk_tolerance
        
    db.commit()
    db.refresh(prefs)
    return {"message": "Preferences updated successfully", "preferences": prefs}

@router.get("/stocks", response_model=List[dict])
def get_saved_stocks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stocks = db.query(SavedStock).filter(SavedStock.user_id == current_user.id).all()
    return [{"id": s.id, "ticker": s.ticker, "company_name": s.company_name, "market": s.market} for s in stocks]

@router.post("/stocks", status_code=status.HTTP_201_CREATED)
def add_saved_stock(payload: StockCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    clean_ticker = payload.ticker.strip().upper()
    existing = db.query(SavedStock).filter(SavedStock.user_id == current_user.id, SavedStock.ticker == clean_ticker).first()
    if existing:
        return {"message": "Stock already in watchlist", "stock": {"id": existing.id, "ticker": existing.ticker, "company_name": existing.company_name, "market": existing.market}}
    
    new_stock = SavedStock(
        user_id=current_user.id,
        ticker=clean_ticker,
        company_name=payload.company_name or clean_ticker,
        market=payload.market or "NSE"
    )
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return {
        "message": "Stock added successfully", 
        "stock": {"id": new_stock.id, "ticker": new_stock.ticker, "company_name": new_stock.company_name, "market": new_stock.market}
    }

@router.delete("/stocks/{stock_id}")
def delete_saved_stock(stock_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    stock = db.query(SavedStock).filter(SavedStock.id == stock_id, SavedStock.user_id == current_user.id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found in watchlist")
    
    db.delete(stock)
    db.commit()
    return {"message": "Stock removed successfully", "id": stock_id}