from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserPreference
from app.schemas import UserPreferenceUpdate, UserPreferenceResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/preferences", tags=["Preferences"])

@router.get("", response_model=UserPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve user preferences for preferred market and analysis period.
    User ID derived strictly from JWT.
    """
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        # Create default if not present
        prefs = UserPreference(
            user_id=current_user.user_id,
            preferred_market="NSE",
            preferred_analysis_period="6 Months"
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs

@router.put("", response_model=UserPreferenceResponse)
def update_preferences(
    pref_in: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update preferred market (NSE, BSE, NASDAQ, NYSE) and analysis period (1 Month, 3 Months, 6 Months, 1 Year, 5 Years).
    User ID derived strictly from JWT.
    """
    prefs = db.query(UserPreference).filter(UserPreference.user_id == current_user.user_id).first()
    if not prefs:
        prefs = UserPreference(
            user_id=current_user.user_id,
            preferred_market=pref_in.preferred_market,
            preferred_analysis_period=pref_in.preferred_analysis_period,
            updated_at=datetime.utcnow()
        )
        db.add(prefs)
    else:
        prefs.preferred_market = pref_in.preferred_market
        prefs.preferred_analysis_period = pref_in.preferred_analysis_period
        prefs.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(prefs)
    return prefs

