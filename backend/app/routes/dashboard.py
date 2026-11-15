from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.models import User


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def dashboard(
    user: User = Depends(get_current_user)
):

    return {
        "message": "Welcome to StockPilot",
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "watchlist_count": 0,
        "research_count": 0,
        "completed_count": 0
    }
