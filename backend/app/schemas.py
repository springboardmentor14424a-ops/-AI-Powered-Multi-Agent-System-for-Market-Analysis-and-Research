from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

ALLOWED_MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"]
ALLOWED_PERIODS = ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"]

# Registration
class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

# Login
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

# Google OAuth
class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = None  # Google ID token if using GIS
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    google_id: Optional[str] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    full_name: str
    email: EmailStr
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Preferences
class PreferenceUpdate(BaseModel):
    preferred_market: str
    default_analysis_period: str

    @field_validator("preferred_market")
    @classmethod
    def validate_market(cls, v):
        if v not in ALLOWED_MARKETS:
            raise ValueError(f"Market must be one of {ALLOWED_MARKETS}")
        return v

    @field_validator("default_analysis_period")
    @classmethod
    def validate_period(cls, v):
        if v not in ALLOWED_PERIODS:
            raise ValueError(f"Period must be one of {ALLOWED_PERIODS}")
        return v

class PreferenceResponse(PreferenceUpdate):
    model_config = ConfigDict(from_attributes=True)

    preference_id: str
    user_id: str
    updated_at: Optional[datetime] = None

# Watchlist
class WatchlistAddRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    market: Optional[str] = None

class WatchlistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved_stock_id: str
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    created_at: datetime
    last_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    currency: Optional[str] = None

# Research Tasks
class ResearchTaskCreate(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    requested_period: Optional[str] = None

class ResearchTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    ticker: str
    company_name: Optional[str] = None
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


# Module 2: Market Data Collection Schemas
class MarketDataCollectRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    market: str = Field(..., description="NSE, BSE, NASDAQ, or NYSE")
    company_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    interval: Optional[str] = "1d"

    @field_validator("market")
    @classmethod
    def validate_market(cls, v):
        v_upper = v.upper()
        if v_upper not in ALLOWED_MARKETS:
            raise ValueError(f"Market must be one of {ALLOWED_MARKETS}")
        return v_upper

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v):
        allowed = ["1d", "1wk", "1mo"]
        if v and v not in allowed:
            raise ValueError(f"Interval must be one of {allowed}")
        return v or "1d"


class MarketDataCollectionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    collection_id: str
    ticker: str
    company_name: Optional[str] = None
    market: str
    country: Optional[str] = None
    interval: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    data_source: str
    record_count: int
    validation_status: str
    retrieved_at: datetime

