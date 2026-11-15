
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# AUTHENTICATION SCHEMAS

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


# RESEARCH SCHEMAS

class ResearchReportResponse(BaseModel):
    report_id: int
    report_content: Optional[str] = None
    summary: Optional[str] = None
    limitations: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchHistoryResponse(BaseModel):
    task_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report: Optional[ResearchReportResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ResearchTaskCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)
    market: str = Field(min_length=1, max_length=30)
    requested_period: str = Field(min_length=1, max_length=30)


# WATCHLIST SCHEMAS

class SavedStockCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=30)


class SavedStockResponse(BaseModel):
    saved_stock_id: int
    ticker: str
    created_at: Optional[datetime] = None
    current_price: Optional[float] = None
    daily_change_percent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# USER PREFERENCES SCHEMAS

class UserPreferenceUpdate(BaseModel):
    market: str = Field(min_length=1, max_length=30)
    research_period: str = Field(min_length=1, max_length=30)


class UserPreferenceResponse(BaseModel):
    preference_id: int
    user_id: int
    market: str
    research_period: str
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
