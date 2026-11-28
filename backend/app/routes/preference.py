
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

from app.schemas.preference import (
    PreferenceCreate,
    PreferenceResponse
)

from app.services.preference_service import (
    get_user_preferences,
    create_user_preferences,
    update_user_preferences
)


router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"]
)


# Create user preferences
@router.post(
    "/",
    response_model=PreferenceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_preferences(
    preference_data: PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        return create_user_preferences(
            preference_data,
            current_user.user_id,
            db
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )


# Get user preferences
@router.get(
    "/",
    response_model=PreferenceResponse
)
def read_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    preferences = get_user_preferences(
        current_user.user_id,
        db
    )

    if not preferences:
        raise HTTPException(
            status_code=404,
            detail="User preferences not found"
        )

    return preferences


# Update user preferences
@router.put(
    "/",
    response_model=PreferenceResponse
)
def update_preferences(
    preference_data: PreferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        return update_user_preferences(
            preference_data,
            current_user.user_id,
            db
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )
