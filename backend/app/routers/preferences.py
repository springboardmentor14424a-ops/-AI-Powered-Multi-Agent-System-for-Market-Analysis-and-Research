
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter()


class PreferencesUpdate(BaseModel):
    preferred_market: str = "NSE"
    preferred_analysis_period: str = "1y"

    preferred_indicators: list[str] = Field(
        default_factory=lambda: ["SMA", "EMA", "RSI", "MACD"]
    )

    preferred_news_window: str = "30 days"
    preferred_risk_view: str = "Balanced"
    preferred_report_format: str = "Markdown"


@router.get("/")
def get_preferences(
    current_user: User = Depends(get_current_user)
):
    return {
        "preferred_market": current_user.preferred_market,
        "preferred_analysis_period": current_user.preferred_analysis_period,
        "preferred_indicators": current_user.preferred_indicators,
        "preferred_news_window": current_user.preferred_news_window,
        "preferred_risk_view": current_user.preferred_risk_view,
        "preferred_report_format": current_user.preferred_report_format
    }


@router.put("/")
def update_preferences(
    preferences: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if preferences.preferred_market not in [
        "NSE", "BSE"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Market must be NSE or BSE"
        )

    if preferences.preferred_analysis_period not in [
        "1mo", "3mo", "6mo", "1y", "5y"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid analysis period"
        )

    valid_indicators = ["SMA", "EMA", "RSI", "MACD"]

    if (
        not preferences.preferred_indicators
        or not all(
            item in valid_indicators
            for item in preferences.preferred_indicators
        )
        or len(set(preferences.preferred_indicators))
        != len(preferences.preferred_indicators)
    ):
        raise HTTPException(
            status_code=400,
            detail="Select at least one valid technical indicator"
        )

    if preferences.preferred_news_window not in [
        "7 days", "30 days", "90 days"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid news window"
        )

    if preferences.preferred_risk_view not in [
        "Conservative", "Balanced", "Aggressive"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid risk view"
        )

    if preferences.preferred_report_format not in [
        "Markdown", "PDF"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid report format"
        )

    current_user.preferred_market = preferences.preferred_market
    current_user.preferred_analysis_period = preferences.preferred_analysis_period
    current_user.preferred_indicators = preferences.preferred_indicators
    current_user.preferred_news_window = preferences.preferred_news_window
    current_user.preferred_risk_view = preferences.preferred_risk_view
    current_user.preferred_report_format = preferences.preferred_report_format

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Preferences saved successfully",
        "preferred_market": current_user.preferred_market,
        "preferred_analysis_period": current_user.preferred_analysis_period,
        "preferred_indicators": current_user.preferred_indicators,
        "preferred_news_window": current_user.preferred_news_window,
        "preferred_risk_view": current_user.preferred_risk_view,
        "preferred_report_format": current_user.preferred_report_format
    }
