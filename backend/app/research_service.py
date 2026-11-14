
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import ResearchTask


def start_research(db: Session, task_id: int):
    task = db.query(ResearchTask).filter(
        ResearchTask.id == task_id
    ).first()

    if not task:
        raise ValueError("Research task not found")

    if task.status != "Pending":
        raise ValueError("Task is not in Pending status")

    task.status = "Processing"
    task.error_message = None

    db.commit()
    db.refresh(task)

    return task


def complete_research(
    db: Session,
    task_id: int,
    report_content: str
):
    task = db.query(ResearchTask).filter(
        ResearchTask.id == task_id
    ).first()

    if not task:
        raise ValueError("Research task not found")

    if task.status != "Processing":
        raise ValueError("Task is not Processing")

    if not report_content.strip():
        raise ValueError("Report content cannot be empty")

    task.report_content = report_content
    task.status = "Completed"
    task.error_message = None

    db.commit()
    db.refresh(task)

    return task


def fail_research(
    db: Session,
    task_id: int,
    error_message: str
):
    task = db.query(ResearchTask).filter(
        ResearchTask.id == task_id
    ).first()

    if not task:
        raise ValueError("Research task not found")

    task.status = "Failed"
    task.error_message = error_message[:2000]
    task.report_content = None

    db.commit()
    db.refresh(task)

    return task
