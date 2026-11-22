from fastapi import APIRouter, Query
from app.services.stock_service import search_stocks, get_stock_history, get_stock_quote
from app.services.ml_service import ml_service

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


@router.get("/{symbol}/analysis")
def full_agent_analysis(symbol: str):
    """Combines all ML-trained agent models for a comprehensive report."""
    hist = get_stock_history(symbol, period="3mo", interval="1d")
    fundamentals = ml_service.analyze_fundamentals(symbol)
    technical = ml_service.analyze_technical(symbol, historical_prices=hist)
    risk = ml_service.analyze_risk(symbol)
    
    return {
        "symbol": symbol.upper(),
        "fundamental_analysis": fundamentals,
        "technical_analysis": technical,
        "risk_assessment": risk,
        "model_version": "v1.0.0-sp500-trained"
    }


@router.get("/models/metrics")
def get_model_metrics():
    """Returns training metrics and accuracy for all trained agent models."""
    return ml_service.training_metrics
