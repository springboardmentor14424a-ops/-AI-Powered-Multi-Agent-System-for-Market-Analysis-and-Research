
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class ResearchTaskCreate(BaseModel):
    ticker: str

    market: Optional[
        Literal["NSE", "BSE", "NASDAQ", "NYSE"]
    ] = None

    requested_period: Optional[
        Literal["1mo", "3mo", "6mo", "1y", "5y"]
    ] = None


class ResearchTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    user_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    report: Optional[dict] = None
