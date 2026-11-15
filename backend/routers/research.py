from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from database.connection import get_db
from models.user import User, ResearchTask, ResearchReport
from schemas.auth import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchTaskUpdate,
    ResearchReportResponse,
)

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/tasks", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: ResearchTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Create a new research task for the current user."""
    task = ResearchTask(
        user_id=current_user.id,
        company_name=payload.company_name,
        ticker=payload.ticker,
        market=payload.market,
        analysis_period=payload.analysis_period,
        status="Pending",
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return ResearchTaskResponse.model_validate(task)


@router.get("/tasks", response_model=list[ResearchTaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResearchTaskResponse]:
    """Return all research tasks for the current user, newest first."""
    result = await db.execute(
        select(ResearchTask)
        .where(ResearchTask.user_id == current_user.id)
        .order_by(ResearchTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [ResearchTaskResponse.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=ResearchTaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Return a single research task (must belong to the current user)."""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this task.",
        )

    return ResearchTaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=ResearchTaskResponse)
async def update_task_status(
    task_id: int,
    payload: ResearchTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchTaskResponse:
    """Update the status of a research task (must belong to the current user)."""
    result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this task.",
        )

    task.status = payload.status
    await db.flush()
    await db.refresh(task)
    return ResearchTaskResponse.model_validate(task)


@router.get("/tasks/{task_id}/report", response_model=ResearchReportResponse)
async def get_task_report(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResearchReportResponse:
    """Return the research report for a task (must belong to the current user)."""
    # First verify the task belongs to the current user
    task_result = await db.execute(
        select(ResearchTask).where(ResearchTask.id == task_id)
    )
    task: ResearchTask | None = task_result.scalar_one_or_none()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this report.",
        )

    # Fetch the report
    report_result = await db.execute(
        select(ResearchReport).where(ResearchReport.task_id == task_id)
    )
    report: ResearchReport | None = report_result.scalar_one_or_none()

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report found for this task.",
        )

    return ResearchReportResponse.model_validate(report)
