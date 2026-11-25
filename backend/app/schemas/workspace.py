from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class StockCreate(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    exchange: str = "NSE"

class StockResponse(BaseModel):
    id: int
    ticker: str
    company_name: Optional[str]
    exchange: str
    added_at: datetime

    class Config:
        from_attributes = True

class PreferenceUpdate(BaseModel):
    risk_tolerance: str
    preferred_market: str
    analysis_period: str

class PreferenceResponse(BaseModel):
    risk_tolerance: str
    preferred_market: str
    analysis_period: str

    class Config:
        from_attributes = True