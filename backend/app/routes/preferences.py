
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, validate_csrf
from app.models import User, UserPreference
from app.schemas import (
    UserPreferenceUpdate,
    UserPreferenceResponse
)
from app.constants import (
    SUPPORTED_MARKETS,
    SUPPORTED_PERIODS,
    DEFAULT_MARKET,
    DEFAULT_RESEARCH_PERIOD
)


router = APIRouter(
    prefix="/api/preferences",
    tags=["User Preferences"]
)


# --------------------------------------------------
# GET USER PREFERENCES
# --------------------------------------------------

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
            market=DEFAULT_MARKET,
            research_period=DEFAULT_RESEARCH_PERIOD
        )

        db.add(preference)
        db.commit()
        db.refresh(preference)

    return preference


# --------------------------------------------------
# UPDATE USER PREFERENCES
# --------------------------------------------------

@router.put("", response_model=UserPreferenceResponse)
def update_preferences(
    data: UserPreferenceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Validate CSRF token before changing data
    validate_csrf(request)

    market = data.market.strip().upper()
    research_period = data.research_period.strip().upper()

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
