
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, SavedStock, ResearchTask


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    watchlist_count = db.query(SavedStock).filter(
        SavedStock.user_id == user.user_id
    ).count()

    research_count = db.query(ResearchTask).filter(
        ResearchTask.user_id == user.user_id
    ).count()

    completed_count = db.query(ResearchTask).filter(
        ResearchTask.user_id == user.user_id,
        ResearchTask.status == "Completed"
    ).count()

    return {
        "message": "Welcome to StockPilot",
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "watchlist_count": watchlist_count,
        "research_count": research_count,
        "completed_count": completed_count
    }
