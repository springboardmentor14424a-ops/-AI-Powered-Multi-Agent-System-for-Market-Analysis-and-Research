from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import PreferenceResponse, PreferenceUpdate
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/preferences", tags=["User Preferences"])

@router.get("", response_model=PreferenceResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        prefs = UserPreference(
            user_id=current_user.user_id,
            preferred_market="NASDAQ",
            default_analysis_period="1 Year"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@router.put("", response_model=PreferenceResponse)
def update_user_preferences(
    pref_in: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        prefs = UserPreference(user_id=current_user.user_id)
        db.add(prefs)

    prefs.preferred_market = pref_in.preferred_market
    prefs.default_analysis_period = pref_in.default_analysis_period
    db.commit()
    db.refresh(prefs)
    return prefs
