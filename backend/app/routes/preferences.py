
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserPreference
from app.schemas import (
    UserPreferenceUpdate,
    UserPreferenceResponse
)


router = APIRouter(
    prefix="/api/preferences",
    tags=["User Preferences"]
)


# Supported preference values
SUPPORTED_MARKETS = ["US", "India"]

SUPPORTED_PERIODS = [
    "1 month",
    "3 months",
    "6 months",
    "1 year"
]


# GET: Retrieve the logged-in user's preferences
@router.get("", response_model=UserPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    preference = (
        db.query(UserPreference)
        .filter(
            UserPreference.user_id == current_user.user_id
        )
        .first()
    )

    # Create default preferences if none exist
    if not preference:
        preference = UserPreference(
            user_id=current_user.user_id,
            market="US",
            research_period="3 months"
        )

        db.add(preference)
        db.commit()
        db.refresh(preference)

    return preference


# PUT: Update the logged-in user's preferences
@router.put("", response_model=UserPreferenceResponse)
def update_preferences(
    data: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    market = data.market.strip()
    research_period = data.research_period.strip()

    if market not in SUPPORTED_MARKETS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported market. Choose US or India."
        )

    if research_period not in SUPPORTED_PERIODS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported research period."
        )

    preference = (
        db.query(UserPreference)
        .filter(
            UserPreference.user_id == current_user.user_id
        )
        .first()
    )

    if not preference:
        preference = UserPreference(
            user_id=current_user.user_id,
            market=market,
            research_period=research_period
        )
        db.add(preference)
    else:
        preference.market = market
        preference.research_period = research_period

    db.commit()
    db.refresh(preference)

    return preference
