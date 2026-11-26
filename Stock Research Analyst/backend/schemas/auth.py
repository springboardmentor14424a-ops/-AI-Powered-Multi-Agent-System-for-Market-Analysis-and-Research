from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ─── User Schemas ───────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse


# ─── Research Task Schemas ───────────────────────────────────────────────────

class ResearchTaskCreate(BaseModel):
    company_name: str
    ticker: str
    market: str
    analysis_period: str


class ResearchTaskResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResearchTaskUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"Pending", "Processing", "Completed", "Failed"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ─── Research Report Schema ──────────────────────────────────────────────────

class ResearchReportResponse(BaseModel):
    id: int
    task_id: int
    report_content: Optional[str]
    generated_at: datetime

    model_config = {"from_attributes": True}


# ─── Google Auth Schema ─────────────────────────────────────────────────────

class GoogleLoginRequest(BaseModel):
    credential: str


# ─── Saved Stock Schemas ─────────────────────────────────────────────────────

class SavedStockCreate(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None


class SavedStockResponse(BaseModel):
    id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    added_at: datetime

    model_config = {"from_attributes": True}


# ─── User Preferences Schemas ───────────────────────────────────────────────

class UserPreferencesUpdate(BaseModel):
    market: str
    analysis_period: str

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        allowed = {"NASDAQ", "NYSE", "NSE", "BSE"}
        if v not in allowed:
            raise ValueError(f"market must be one of {allowed}")
        return v

    @field_validator("analysis_period")
    @classmethod
    def validate_analysis_period(cls, v: str) -> str:
        allowed = {"1 Month", "3 Months", "6 Months", "1 Year", "5 Years"}
        if v not in allowed:
            raise ValueError(f"analysis_period must be one of {allowed}")
        return v


class UserPreferencesResponse(BaseModel):
    id: int
    user_id: int
    market: str
    analysis_period: str
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Stock Schemas ───────────────────────────────────────────────────────────

from schemas.stock import StockSearchResult, StockQuoteResponse

