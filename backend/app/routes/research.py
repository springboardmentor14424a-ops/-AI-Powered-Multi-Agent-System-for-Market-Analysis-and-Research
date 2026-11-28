
from typing import List
from app.services.research_execution_service import execute_research_task

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

from app.schemas.research_task import (
    ResearchTaskCreate,
    ResearchTaskResponse
)

from app.services.research_task_service import (
    create_research_task,
    get_user_research_history,
    get_research_task_by_id
)


router = APIRouter(
    prefix="/research",
    tags=["Research History"]
)


# 1. Create a new research task
@router.post(
    "/",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_201_CREATED
)
def create_task(
    task_data: ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        task = create_research_task(
            task_data,
            current_user.user_id,
            db
        )
        return task

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to create research task"
        )


# 2. Get all research tasks of logged-in user
@router.get(
    "/history",
    response_model=List[ResearchTaskResponse]
)
def get_research_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_research_history(
        current_user.user_id,
        db
    )


# 3. Get one research task using task ID
@router.get(
    "/{task_id}",
    response_model=ResearchTaskResponse
)
def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = get_research_task_by_id(
        task_id,
        current_user.user_id,
        db
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    return task

# 4. Execute stock research
@router.post(
    "/{task_id}/execute",
    response_model=ResearchTaskResponse
)
def execute_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = execute_research_task(
        task_id,
        current_user.user_id,
        db
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Research task not found"
        )

    return task

