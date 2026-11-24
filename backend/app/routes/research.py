
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.auth import get_current_user, validate_csrf
from app.models import User, ResearchTask
from app.schemas import (
    ResearchTaskCreate,
    ResearchHistoryResponse
)
from app.constants import (
    SUPPORTED_MARKETS,
    SUPPORTED_PERIODS
)


router = APIRouter(
    prefix="/api/research",
    tags=["Research History"]
)


# --------------------------------------------------
# GET USER RESEARCH HISTORY
# --------------------------------------------------

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


# --------------------------------------------------
# CREATE RESEARCH TASK
# --------------------------------------------------

@router.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED
)
def create_research_task(
    data: ResearchTaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Validate CSRF token before changing data
    validate_csrf(request)

    ticker = data.ticker.strip().upper()
    market = data.market.strip().upper()
    research_period = data.requested_period.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock ticker cannot be empty."
        )

    if market not in SUPPORTED_MARKETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported exchange. Choose NSE, BSE, NASDAQ or NYSE."
        )

    if research_period not in SUPPORTED_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported research period. Choose 1M, 3M, 6M, 1Y or 5Y."
        )

    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=ticker,
        market=market,
        requested_period=research_period,
        status="Pending"
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "message": "Research task created successfully",
        "task_id": task.task_id,
        "ticker": task.ticker,
        "market": task.market,
        "requested_period": task.requested_period,
        "status": task.status
    }
