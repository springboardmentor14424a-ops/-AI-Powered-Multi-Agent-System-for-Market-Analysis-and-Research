
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import  Optional


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    message: str


# Request to create a research task
class ResearchTaskCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=150)
    stock_ticker: str = Field(min_length=1, max_length=20)
    market: str = Field(min_length=2, max_length=50)
    analysis_period: str = Field(min_length=2, max_length=50)


# Response for research history
class ResearchTaskResponse(BaseModel):
    id: int
    company_name: str
    stock_ticker: str
    market: str
    analysis_period: str
    research_date: datetime
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Response for generated report
class ResearchReportResponse(BaseModel):
    id: int
    company_name: str
    stock_ticker: str
    status: str
    report_content: str

    model_config = ConfigDict(from_attributes=True)

class StockSearchResult(BaseModel):
    symbol: str
    company_name: str


class SavedStockCreate(BaseModel):
    stock_ticker: str


class SavedStockResponse(BaseModel):
    id: int
    company_name: str
    stock_ticker: str
    saved_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# MODULE 6: USER PREFERENCES SCHEMAS
# ==========================================

SUPPORTED_MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"]

SUPPORTED_PERIODS = [
    "1 Month",
    "3 Months",
    "6 Months",
    "1 Year",
    "5 Years"
]


class UserPreferencesCreate(BaseModel):
    market: str = "NASDAQ"
    analysis_period: str = "3 Months"

    @field_validator("market")
    @classmethod
    def validate_market(cls, value):
        value = value.upper().strip()

        if value not in SUPPORTED_MARKETS:
            raise ValueError("Unsupported market")

        return value

    @field_validator("analysis_period")
    @classmethod
    def validate_period(cls, value):
        value = value.strip()

        if value not in SUPPORTED_PERIODS:
            raise ValueError("Unsupported analysis period")

        return value


class UserPreferencesResponse(BaseModel):
    id: int
    user_id: int
    market: str
    analysis_period: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
