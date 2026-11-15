from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import ResearchTask, User
from ..schemas import ResearchCreate, ResearchDetailOut, ResearchOut
from ..stock_service import resolve
from ..workflow_stub import run_research_workflow
from .preferences import get_or_create_preferences

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchOut, status_code=status.HTTP_201_CREATED)
def start_research(
    payload: ResearchCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    prefs = get_or_create_preferences(db, user.user_id)
    market = payload.market or prefs.market
    period = payload.analysis_period or prefs.analysis_period

    stock = resolve(payload.ticker, market)
    if stock is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{payload.ticker}' is not a supported symbol on {market}.",
        )

    task = ResearchTask(
        user_id=user.user_id,  # from the verified JWT
        ticker=stock["ticker"],
        company_name=stock["name"],
        market=market,
        analysis_period=period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background.add_task(run_research_workflow, task.task_id)
    return task


@router.get("", response_model=list[ResearchOut])
def research_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Only the logged-in user's tasks, newest first."""
    stmt = (
        select(ResearchTask)
        .where(ResearchTask.user_id == user.user_id)
        .order_by(ResearchTask.created_at.desc(), ResearchTask.task_id.desc())
    )
    return db.scalars(stmt).all()


@router.get("/{task_id}", response_model=ResearchDetailOut)
def research_detail(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = db.scalar(
        select(ResearchTask).where(ResearchTask.task_id == task_id, ResearchTask.user_id == user.user_id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Research task not found.")
    return task
