from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from database.connection import get_db
from models.user import User, UserPreferences
from schemas.auth import UserPreferencesUpdate, UserPreferencesResponse

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse)
@router.get("/", response_model=UserPreferencesResponse, include_in_schema=False)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """Get user preferences. Returns defaults if none exist yet."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs: UserPreferences | None = result.scalar_one_or_none()

    if prefs is None:
        # Create default preferences
        prefs = UserPreferences(
            user_id=current_user.id,
            market="NASDAQ",
            analysis_period="1 Year",
        )
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)

    return UserPreferencesResponse.model_validate(prefs)


@router.put("", response_model=UserPreferencesResponse)
@router.put("/", response_model=UserPreferencesResponse, include_in_schema=False)
async def update_preferences(
    payload: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPreferencesResponse:
    """Create or update user preferences (upsert)."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs: UserPreferences | None = result.scalar_one_or_none()

    if prefs:
        prefs.market = payload.market
        prefs.analysis_period = payload.analysis_period
    else:
        prefs = UserPreferences(
            user_id=current_user.id,
            market=payload.market,
            analysis_period=payload.analysis_period,
        )
        db.add(prefs)

    await db.flush()
    await db.refresh(prefs)
    return UserPreferencesResponse.model_validate(prefs)
