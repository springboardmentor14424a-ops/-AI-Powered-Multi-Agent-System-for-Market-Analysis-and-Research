from fastapi import APIRouter, Query
from app.services.stock_service import search_stocks, get_stock_history, get_stock_quote
from app.services.ratio_service import (
    fetch_and_calculate_real_financial_ratios,
    compute_all_financial_ratios,
)
from app.schemas.ratios import RatioInputForm
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


@router.get("/{symbol}/ratios")
def get_financial_ratios(symbol: str):
    """
    Retrieves real financial statement data and calculates:
    - P/E (Price-to-Earnings)
    - EPS (Earnings Per Share)
    - ROE (Return on Equity)
    - Debt-to-Equity (D/E)
    - Current Ratio
    - Net Profit Margin
    - ROA (Return on Assets)
    """
    return fetch_and_calculate_real_financial_ratios(symbol)


@router.post("/calculate-ratios")
def calculate_custom_ratios(body: RatioInputForm):
    """
    Calculates all 7 financial ratios from explicit financial metrics
    with complete input validation and edge-case handling.
    """
    return compute_all_financial_ratios(
        price=body.price,
        net_income=body.net_income,
        shares_outstanding=body.shares_outstanding,
        total_shareholder_equity=body.total_shareholder_equity,
        total_debt=body.total_debt,
        current_assets=body.current_assets,
        current_liabilities=body.current_liabilities,
        total_revenue=body.total_revenue,
        total_assets=body.total_assets,
        eps_override=body.eps,
    )


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
