"""Research workflow: moves a task pending -> processing -> completed/failed.

`generate_report` runs the four agents (app/agents) on real market data. The agents
degrade gracefully: if only some data is available the report says which parts are
missing; if there's no price data at all the task is recorded as failed with a clear message.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import func, update

from .agents import AnalysisError, run_analysis
from .database import SessionLocal
from .models import COMPLETED, FAILED, PENDING, PROCESSING, ResearchTask

log = logging.getLogger(__name__)

GENERIC_FAILURE = "The analysis could not be completed. Please try again."


def generate_report(task: ResearchTask) -> str:
    return run_analysis(task)


def _record_failure(db, task_id: int, message: str) -> None:
    db.rollback()
    task = db.get(ResearchTask, task_id)
    task.status = FAILED
    task.error = message
    task.completed_at = datetime.now(timezone.utc)
    db.commit()


def run_workflow(task_id: int) -> None:
    """Runs in a background task, with its own database session."""
    with SessionLocal() as db:
        task = db.get(ResearchTask, task_id)
        if task is None:
            return
        task.status = PROCESSING
        db.commit()

        try:
            report = generate_report(task)
        except AnalysisError as e:
            # Written for the user (no internals), so it's safe to store and show.
            _record_failure(db, task_id, str(e))
            return
        except Exception:
            # Full details go to the server log; the user gets a clear, safe message.
            log.exception("Research task %s failed", task_id)
            _record_failure(db, task_id, GENERIC_FAILURE)
            return

        task.status = COMPLETED
        task.report = report
        task.completed_at = datetime.now(timezone.utc)
        db.commit()


def mark_interrupted_tasks() -> None:
    """On startup, tasks left pending/processing by a stopped server can never
    finish, so record them as failed instead of leaving them spinning forever."""
    with SessionLocal() as db:
        db.execute(
            update(ResearchTask)
            .where(ResearchTask.status.in_([PENDING, PROCESSING]))
            .values(
                status=FAILED,
                error="Interrupted by a server restart. Please run the analysis again.",
                completed_at=func.now(),
            )
        )
        db.commit()
