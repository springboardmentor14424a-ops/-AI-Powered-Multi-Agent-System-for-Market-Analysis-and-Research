
from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference
from app.schemas.preference import PreferenceCreate


# Get user preferences
def get_user_preferences(user_id: int, db: Session):

    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()

    return preferences


# Create user preferences
def create_user_preferences(
    preference_data: PreferenceCreate,
    user_id: int,
    db: Session
):

    # Check whether preferences already exist
    existing = get_user_preferences(user_id, db)

    if existing:
        raise ValueError("User preferences already exist")

    new_preference = UserPreference(
        user_id=user_id,
        preferred_market=preference_data.preferred_market,
        default_analysis_period=preference_data.default_analysis_period
    )

    try:
        db.add(new_preference)
        db.commit()
        db.refresh(new_preference)

        return new_preference

    except Exception:
        db.rollback()
        raise


# Update user preferences
def update_user_preferences(
    preference_data: PreferenceCreate,
    user_id: int,
    db: Session
):

    preferences = get_user_preferences(user_id, db)

    if not preferences:
        raise ValueError("User preferences not found")

    preferences.preferred_market = preference_data.preferred_market
    preferences.default_analysis_period = (
        preference_data.default_analysis_period
    )

    try:
        db.commit()
        db.refresh(preferences)

        return preferences

    except Exception:
        db.rollback()
        raise

