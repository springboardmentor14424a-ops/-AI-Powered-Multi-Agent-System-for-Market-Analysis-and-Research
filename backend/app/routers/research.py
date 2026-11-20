from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import ResearchTask, User, UserPreference
from ..schemas import ResearchCreate, ResearchTaskOut

router = APIRouter(prefix="/research", tags=["research"])


@router.get("", response_model=list[ResearchTaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ResearchTask)
        .filter(ResearchTask.user_id == current_user.user_id)
        .order_by(ResearchTask.created_at.desc())
        .limit(50)
        .all()
    )


@router.post("", response_model=ResearchTaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: ResearchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.get(UserPreference, current_user.user_id)
    market = data.market or (pref.market if pref else "NSE")
    period = data.requested_period or (pref.default_period if pref else "1Y")

    task = ResearchTask(
        user_id=current_user.user_id,
        ticker=data.ticker,
        market=market,
        requested_period=period,
        status="Pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task