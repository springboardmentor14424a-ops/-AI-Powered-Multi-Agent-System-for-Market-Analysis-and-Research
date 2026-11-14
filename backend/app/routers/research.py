
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.research_task import ResearchTask
from app.models.research_report import ResearchReport
from app.schemas.research import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchReportResponse
)


router = APIRouter()


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
    new_task = ResearchTask(
        user_id=current_user.user_id,
        company_name=task_data.company_name.strip(),
        ticker=task_data.ticker.strip().upper(),
        market=task_data.market.strip(),
        analysis_period=task_data.analysis_period.strip(),
        status="PENDING"
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


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
