from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/preferences", tags=["preferences"])

DEFAULT_MARKET = "NASDAQ"
DEFAULT_PERIOD = "1Y"


def get_or_create_preferences(db: Session, user_id: int) -> UserPreference:
    prefs = db.get(UserPreference, user_id)
    if prefs is None:
        prefs = UserPreference(user_id=user_id, market=DEFAULT_MARKET, analysis_period=DEFAULT_PERIOD)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesOut)
def read_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_or_create_preferences(db, user.user_id)


@router.put("", response_model=PreferencesOut)
def update_preferences(
    payload: PreferencesIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    prefs = get_or_create_preferences(db, user.user_id)
    prefs.market = payload.market
    prefs.analysis_period = payload.analysis_period
    db.commit()
    db.refresh(prefs)
    return prefs
