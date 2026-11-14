from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import PENDING, ResearchTask, User
from ..schemas import ResearchDetail, ResearchIn, ResearchSummary
from ..workflow import run_workflow

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("", response_model=ResearchSummary, status_code=status.HTTP_201_CREATED)
def start_research(
    payload: ResearchIn,
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # The owner is the user from the verified JWT, never anything in the request body.
    task = ResearchTask(
        user_id=user.id,
        company_name=payload.company_name,
        ticker=payload.ticker,
        market=payload.market,
        analysis_period=payload.analysis_period,
        status=PENDING,
    )
    db.add(task)
    db.commit()
    background.add_task(run_workflow, task.id)
    return task


@router.get("", response_model=list[ResearchSummary])
def list_research(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only the logged-in user's tasks, newest first."""
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.user_id == user.id)
        .order_by(ResearchTask.created_at.desc(), ResearchTask.id.desc())
        .limit(200)
    )
    return db.scalars(stmt).all()


@router.get("/{task_id}", response_model=ResearchDetail)
def get_research(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Filtering by user_id too means another user's task looks exactly like a missing one.
    task = db.scalar(
        select(ResearchTask).where(ResearchTask.id == task_id, ResearchTask.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Research task not found.")
    return task
