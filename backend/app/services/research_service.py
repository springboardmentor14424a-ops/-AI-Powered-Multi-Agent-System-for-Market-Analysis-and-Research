
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.research_task import ResearchTask
from app.models.research_report import ResearchReport


def mark_research_processing(
    db: Session,
    task_id: UUID
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    if task.status != "PENDING":
        raise HTTPException(
            status_code=409,
            detail="Research task cannot be started in its current status"
        )

    task.status = "PROCESSING"

    db.commit()
    db.refresh(task)

    return task


def complete_research_task(
    db: Session,
    task_id: UUID,
    report_content: str,
    summary: str = None,
    limitations: str = None
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    if task.status != "PROCESSING":
        raise HTTPException(
            status_code=409,
            detail="Only processing tasks can be completed"
        )

    if not report_content.strip():
        raise HTTPException(
            status_code=400,
            detail="Report content cannot be empty"
        )

    existing_report = db.query(ResearchReport).filter(
        ResearchReport.task_id == task.task_id
    ).first()

    if existing_report:
        raise HTTPException(
            status_code=409,
            detail="A report already exists for this task"
        )

    report = ResearchReport(
        task_id=task.task_id,
        report_content=report_content,
        summary=summary,
        limitations=limitations
    )

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)

    try:
        db.add(report)
        db.commit()
        db.refresh(report)
        db.refresh(task)

    except Exception:
        db.rollback()
        raise

    return report


def fail_research_task(
    db: Session,
    task_id: UUID
):
    task = db.query(ResearchTask).filter(
        ResearchTask.task_id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    if task.status != "PROCESSING":
        raise HTTPException(
            status_code=409,
            detail="Only processing tasks can be marked as failed"
        )

    task.status = "FAILED"
    task.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(task)

    return task
