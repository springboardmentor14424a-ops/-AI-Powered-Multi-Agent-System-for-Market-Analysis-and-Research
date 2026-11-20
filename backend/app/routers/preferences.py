from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User, UserPreference
from ..schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/preferences", tags=["preferences"])

DEFAULT_MARKET = "NSE"
DEFAULT_PERIOD = "1Y"


@router.get("", response_model=PreferencesOut)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.get(UserPreference, current_user.user_id)
    if pref is None:
        return PreferencesOut(market=DEFAULT_MARKET, default_period=DEFAULT_PERIOD)
    return pref


@router.put("", response_model=PreferencesOut)
def save_preferences(
    data: PreferencesIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pref = db.get(UserPreference, current_user.user_id)
    if pref is None:
        pref = UserPreference(
            user_id=current_user.user_id,
            market=data.market,
            default_period=data.default_period,
        )
        db.add(pref)
    else:
        pref.market = data.market
        pref.default_period = data.default_period
    db.commit()
    db.refresh(pref)
    return pref