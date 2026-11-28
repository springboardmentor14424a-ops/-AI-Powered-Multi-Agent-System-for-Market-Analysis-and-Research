
from pydantic import BaseModel, Field
from typing import Literal


class PreferenceCreate(BaseModel):
    preferred_market: Literal["NSE", "BSE", "NASDAQ", "NYSE"] = "NSE"

    default_analysis_period: Literal[
        "1mo", "3mo", "6mo", "1y", "5y"
    ] = "1y"


class PreferenceResponse(BaseModel):
    preference_id: int
    user_id: int
    preferred_market: str
    default_analysis_period: str

    model_config = {"from_attributes": True}
