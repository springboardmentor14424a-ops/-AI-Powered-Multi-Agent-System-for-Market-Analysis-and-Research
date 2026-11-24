"""
Fundamental Analysis Router
Agent 3: Endpoints for executing fundamental evaluations, retrieving analysis history,
and managing saved fundamental reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime, timezone

from app.database import get_db
from app.models import User, FundamentalAnalysis
from app.schemas import FundamentalAnalyzeRequest, FundamentalAnalysisSummary
from app.dependencies import get_current_user
from app.services.fundamental_agent import run_fundamental_agent_analysis

router = APIRouter(prefix="/api/fundamental", tags=["Agent 3: Fundamental Analysis"])

@router.post("/analyze", status_code=status.HTTP_201_CREATED)
def perform_fundamental_analysis(
    payload: FundamentalAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes deep fundamental analysis:
    - Revenue & Earnings YoY growth
    - Profitability metrics (Gross, Operating, Net margins, ROE, ROA)
    - Debt & Financial stability (Debt/Equity, Current Ratio, Solvency Grade)
    - Valuation ratios (P/E, P/B, EV/EBITDA)
    - Multi-year historical performance
    - Industry peer benchmarking
    - Missing & inconsistent data audit
    - AI-grade synthesis narrative and health score
    Persists the structured report to PostgreSQL.
    """
    analysis_data = run_fundamental_agent_analysis(
        ticker=payload.ticker,
        market=payload.market,
        company_name=payload.company_name
    )

    health = analysis_data.get("health_score", {})
    score = health.get("score", 50.0)
    verdict = health.get("verdict", "Moderate Financial Performance")

    db_entry = FundamentalAnalysis(
        user_id=current_user.user_id,
        ticker=analysis_data["ticker"],
        company_name=analysis_data["company_name"],
        market=analysis_data["market"],
        currency=analysis_data["currency"],
        reporting_period=analysis_data["reporting_period"],
        data_source=analysis_data["data_source"],
        retrieved_at=datetime.now(timezone.utc),
        overall_score=score,
        overall_verdict=verdict,
        metrics=json.dumps({
            "revenue_earnings_analysis": analysis_data["revenue_earnings_analysis"],
            "profitability_analysis": analysis_data["profitability_analysis"],
            "debt_stability_analysis": analysis_data["debt_stability_analysis"],
            "valuation_analysis": analysis_data["valuation_analysis"],
        }),
        historical_trends=json.dumps(analysis_data["historical_trends"]),
        peer_comparison=json.dumps(analysis_data["peer_comparison"]),
        risk_observations=json.dumps(analysis_data["debt_stability_analysis"]["financial_risks"]),
        missing_data_audit=json.dumps(analysis_data["missing_data_audit"]),
        executive_summary=analysis_data["executive_summary"],
        created_at=datetime.now(timezone.utc)
    )

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return {
        "analysis_id": db_entry.analysis_id,
        **analysis_data
    }

@router.get("/history", response_model=List[FundamentalAnalysisSummary])
def get_fundamental_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves all past fundamental analyses run by the authenticated user."""
    records = db.query(FundamentalAnalysis).filter(
        FundamentalAnalysis.user_id == current_user.user_id
    ).order_by(FundamentalAnalysis.retrieved_at.desc()).all()
    return records

@router.get("/{analysis_id}")
def get_fundamental_analysis_detail(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full details of a saved fundamental analysis report."""
    rec = db.query(FundamentalAnalysis).filter(
        FundamentalAnalysis.analysis_id == analysis_id,
        FundamentalAnalysis.user_id == current_user.user_id
    ).first()

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fundamental analysis report not found or unauthorized."
        )

    metrics_obj = json.loads(rec.metrics) if rec.metrics else {}
    health = {
        "score": rec.overall_score,
        "grade": "A" if rec.overall_score >= 80 else "B" if rec.overall_score >= 65 else "C" if rec.overall_score >= 50 else "D",
        "verdict": rec.overall_verdict,
        "risk_level": "Low" if rec.overall_score >= 80 else "Low-to-Moderate" if rec.overall_score >= 65 else "Moderate" if rec.overall_score >= 50 else "High"
    }

    return {
        "analysis_id": rec.analysis_id,
        "ticker": rec.ticker,
        "company_name": rec.company_name,
        "market": rec.market,
        "currency": rec.currency,
        "reporting_period": rec.reporting_period,
        "data_source": rec.data_source,
        "retrieved_at_utc": rec.retrieved_at.isoformat(),
        "retrieved_at_local": rec.retrieved_at.strftime("%Y-%m-%d %H:%M:%S"),
        "health_score": health,
        "revenue_earnings_analysis": metrics_obj.get("revenue_earnings_analysis", {}),
        "profitability_analysis": metrics_obj.get("profitability_analysis", {}),
        "debt_stability_analysis": metrics_obj.get("debt_stability_analysis", {}),
        "valuation_analysis": metrics_obj.get("valuation_analysis", {}),
        "historical_trends": json.loads(rec.historical_trends) if rec.historical_trends else [],
        "peer_comparison": json.loads(rec.peer_comparison) if rec.peer_comparison else {},
        "missing_data_audit": json.loads(rec.missing_data_audit) if rec.missing_data_audit else {},
        "executive_summary": rec.executive_summary
    }

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fundamental_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a saved fundamental analysis report."""
    rec = db.query(FundamentalAnalysis).filter(
        FundamentalAnalysis.analysis_id == analysis_id,
        FundamentalAnalysis.user_id == current_user.user_id
    ).first()

    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fundamental analysis report not found."
        )

    db.delete(rec)
    db.commit()
    return None
