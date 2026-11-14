from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/api/preferences", tags=["preferences"])

DEFAULT_MARKET = "NASDAQ"
DEFAULT_PERIOD = "6 months"


@router.get("", response_model=PreferencesOut)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pref = db.get(UserPreference, user.id)
    if pref is None:  # nothing saved yet -> sensible defaults
        return PreferencesOut(market=DEFAULT_MARKET, analysis_period=DEFAULT_PERIOD)
    return PreferencesOut(market=pref.preferred_market, analysis_period=pref.default_analysis_period)


@router.put("", response_model=PreferencesOut)
def save_preferences(
    payload: PreferencesIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    pref = db.get(UserPreference, user.id)
    if pref is None:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
    pref.preferred_market = payload.market
    pref.default_analysis_period = payload.analysis_period
    db.commit()
    return PreferencesOut(market=pref.preferred_market, analysis_period=pref.default_analysis_period)
