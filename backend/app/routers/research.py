
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.research_task import ResearchTask
from app.models.research_report import ResearchReport
from app.services.yahoo_finance import get_stock_history
from app.schemas.research import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchReportResponse
)


router = APIRouter()


def _normalize_ticker_for_market(ticker: str, market: str) -> str:
    ticker = ticker.strip().upper()
    market = market.strip().upper()

    if market == "NSE":
        if ticker.endswith(".BO"):
            ticker = ticker[:-3]
        if not ticker.endswith(".NS"):
            ticker = ticker + ".NS"
    elif market == "BSE":
        if ticker.endswith(".NS"):
            ticker = ticker[:-3]
        if not ticker.endswith(".BO"):
            ticker = ticker + ".BO"
    else:  # NASDAQ or NYSE
        if ticker.endswith(".NS") or ticker.endswith(".BO"):
            ticker = ticker[:-3]
        ticker = ticker.split(".")[0]

    return ticker


# Create a new research task
@router.post(
    "/",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_201_CREATED
)
def create_research_task(
    task_data: ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    retrieval_timestamp = task_data.data_retrieved_at

    # If client did not supply a data retrieval timestamp, retrieve stock data to capture it
    if retrieval_timestamp is None:
        try:
            formatted_ticker = _normalize_ticker_for_market(
                task_data.ticker,
                task_data.market
            )
            period = task_data.analysis_period.strip()
            if period not in ["1mo", "3mo", "6mo", "1y", "5y"]:
                period = "1y"

            history_result = get_stock_history(formatted_ticker, period=period)
            if history_result.get("success") and history_result.get("retrieved_at"):
                retrieval_timestamp = datetime.fromisoformat(history_result["retrieved_at"])
        except Exception:
            retrieval_timestamp = None

    new_task = ResearchTask(
        user_id=current_user.user_id,
        company_name=task_data.company_name.strip(),
        ticker=task_data.ticker.strip().upper(),
        market=task_data.market.strip(),
        analysis_period=task_data.analysis_period.strip(),
        status="PENDING",
        data_retrieved_at=retrieval_timestamp
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# Refresh / re-retrieve market data for an existing research task
@router.post(
    "/{task_id}/refresh-data",
    response_model=ResearchTaskResponse
)
def refresh_task_market_data(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    formatted_ticker = _normalize_ticker_for_market(
        task.ticker,
        task.market
    )
    period = task.analysis_period.strip()
    if period not in ["1mo", "3mo", "6mo", "1y", "5y"]:
        period = "1y"

    history_result = get_stock_history(formatted_ticker, period=period)
    if not history_result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=history_result.get("message", "Unable to retrieve stock data")
        )

    if history_result.get("retrieved_at"):
        task.data_retrieved_at = datetime.fromisoformat(history_result["retrieved_at"])
        db.commit()
        db.refresh(task)

    return task


# Retrieve only the logged-in user's research history
@router.get(
    "/history",
    response_model=list[ResearchTaskResponse]
)
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ResearchTask).filter(
        ResearchTask.user_id == current_user.user_id
    ).order_by(
        ResearchTask.started_at.desc()
    ).all()


# Retrieve a completed report belonging to the logged-in user
@router.get(
    "/{task_id}/report",
    response_model=ResearchReportResponse
)
def get_research_report(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id,
        ResearchTask.user_id == current_user.user_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    if task.status != "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail="Research report is not completed yet"
        )

    report = db.query(ResearchReport).filter(
        ResearchReport.task_id == task.task_id
    ).first()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Research report not found"
        )

    return report
