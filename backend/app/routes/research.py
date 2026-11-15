from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResearchReportResponse(BaseModel):
    report_id: int
    report_content: Optional[str] = None
    summary: Optional[str] = None
    limitations: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchHistoryResponse(BaseModel):
    task_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report: Optional[ResearchReportResponse] = None

    model_config = ConfigDict(from_attributes=True)


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.auth import get_current_user
from app.models import User, ResearchTask
from app.schemas import (
    ResearchTaskCreate,
    ResearchHistoryResponse
)


router = APIRouter(
    prefix="/api/research",
    tags=["Research History"]
)


@router.get(
    "/history",
    response_model=list[ResearchHistoryResponse]
)
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    research_tasks = (
        db.query(ResearchTask)
        .options(selectinload(ResearchTask.research_report))
        .filter(
            ResearchTask.user_id == current_user.user_id
        )
        .order_by(ResearchTask.created_at.desc())
        .all()
    )

    return [
        {
            "task_id": task.task_id,
            "ticker": task.ticker,
            "market": task.market,
            "requested_period": task.requested_period,
            "status": task.status,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
            "report": task.research_report
        }
        for task in research_tasks
    ]

@router.post("/tasks", status_code=201)
def create_research_task(
    data: ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=data.ticker.upper(),
        market=data.market,
        requested_period=data.requested_period,
        status="Pending"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "message": "Research task created successfully",
        "task_id": task.task_id,
        "ticker": task.ticker,
        "status": task.status
    }

