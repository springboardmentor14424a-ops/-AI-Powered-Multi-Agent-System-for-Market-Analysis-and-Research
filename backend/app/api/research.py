from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.preference import UserPreference
from app.models.task import ResearchTask
from app.models.user import User
from app.services.market_data import (
    fetch_market_bundle,
    normalize_market,
    normalize_period,
    run_multi_agent_analysis,
)

router = APIRouter(prefix="/api/research", tags=["Research"])


class ResearchRunRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=30)
    market: str | None = Field(default=None, max_length=50)
    analysis_period: str | None = Field(default=None, max_length=50)
    risk_tolerance: str | None = Field(default=None, max_length=50)


@router.get("/history")
@router.get("/tasks")
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )
    return {
        "tasks": [
            {
                "id": t.id,
                "ticker": t.ticker,
                "market": t.market,
                "analysis_period": t.analysis_period,
                "status": t.status,
                "summary": t.summary,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_stock_research(
    payload: ResearchRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()

    raw_market = payload.market or (pref.preferred_market if pref else "NASDAQ")
    raw_period = payload.analysis_period or (pref.analysis_period if pref else "1 Year")
    raw_risk = payload.risk_tolerance or (
        getattr(pref, "risk_tolerance", None) if pref else "Moderate"
    )

    try:
        normalized_market = normalize_market(raw_market)
        period_label, _ = normalize_period(raw_period)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    clean_input_ticker = payload.ticker.strip().upper().removesuffix(".NS").removesuffix(".BO")

    task = ResearchTask(
        user_id=current_user.id,
        ticker=clean_input_ticker,
        market=normalized_market,
        analysis_period=period_label,
        status="Processing",
        summary="Running multi-agent market data collection and analysis...",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        bundle = fetch_market_bundle(
            symbol=clean_input_ticker,
            market=normalized_market,
            period=period_label,
        )
        report = run_multi_agent_analysis(bundle=bundle, risk_tolerance=raw_risk or "Moderate")

        task.ticker = bundle["ticker"]
        task.status = "Completed"
        task.summary = report["cio_synthesis"]["summary"]
        db.commit()
        db.refresh(task)

        return {
            "task": {
                "id": task.id,
                "ticker": task.ticker,
                "symbol": bundle["symbol"],
                "market": task.market,
                "analysis_period": task.analysis_period,
                "status": task.status,
                "summary": task.summary,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            },
            "report": report,
            "market_data": bundle,
        }

    except ValueError as exc:
        task.status = "Failed"
        task.summary = f"Validation error: {exc}"
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    except Exception as exc:
        task.status = "Failed"
        task.summary = f"Research workflow failed: {exc}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Research workflow failed: {exc}",
        ) from exc