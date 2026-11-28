
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.research_task import ResearchTask
from app.models.user_preference import UserPreference
from app.schemas.research_task import ResearchTaskCreate


# 1. Create a new research task using user preferences
def create_research_task(
    task_data: ResearchTaskCreate,
    user_id: int,
    db: Session
):
    # Fetch saved preferences of the logged-in user
    preferences = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )

    # Use explicitly selected values first.
    # Otherwise, use saved preferences.
    # If no preferences exist, use default values.
    selected_market = (
        task_data.market
        or (preferences.preferred_market if preferences else "NSE")
    )

    selected_period = (
        task_data.requested_period
        or (
            preferences.default_analysis_period
            if preferences else "1y"
        )
    )

    task = ResearchTask(
        user_id=user_id,
        ticker=task_data.ticker.strip().upper(),
        market=selected_market,
        requested_period=selected_period,
        status="Pending"
    )

    try:
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    except Exception:
        db.rollback()
        raise


# 2. Get research history of a particular user
def get_user_research_history(
    user_id: int,
    db: Session
):
    return (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == user_id)
        .order_by(ResearchTask.created_at.desc())
        .all()
    )


# 3. Update research task status
def update_research_task_status(
    task_id: int,
    user_id: int,
    status: str,
    db: Session
):
    task = (
        db.query(ResearchTask)
        .filter(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == user_id
        )
        .first()
    )

    if task is None:
        return None

    allowed_statuses = [
        "Pending",
        "Processing",
        "Completed",
        "Failed"
    ]

    if status not in allowed_statuses:
        raise ValueError("Invalid research task status")

    task.status = status

    if status in ["Completed", "Failed"]:
        task.completed_at = datetime.now(timezone.utc)
    else:
        task.completed_at = None

    try:
        db.commit()
        db.refresh(task)
        return task

    except Exception:
        db.rollback()
        raise


# 4. Get one research task using task ID
def get_research_task_by_id(
    task_id: int,
    user_id: int,
    db: Session
):
    return (
        db.query(ResearchTask)
        .filter(
            ResearchTask.task_id == task_id,
            ResearchTask.user_id == user_id
        )
        .first()
    )
