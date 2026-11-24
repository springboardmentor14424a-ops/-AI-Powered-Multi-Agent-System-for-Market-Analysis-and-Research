
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
    market: str = Field(min_length=1, max_length=30)


class SavedStockResponse(BaseModel):
    saved_stock_id: int
    ticker: str
    market: str
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



# --------------------------------------------------
# STOCK MARKET DATA SCHEMAS
# --------------------------------------------------

class StockProfileResponse(BaseModel):
    ticker: str
    provider_symbol: str
    company_name: str
    market: str

    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    website: Optional[str] = None

    market_cap: Optional[float] = None
    employees: Optional[int] = None

    data_provider: str
    retrieved_at: datetime


# --------------------------------------------------
# HISTORICAL STOCK DATA SCHEMAS
# --------------------------------------------------

class StockHistoryRecord(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: Optional[float] = None
    volume: int



class StockHistoryValidation(BaseModel):
    is_valid: bool
    valid_rows: int
    invalid_rows: int
    missing_values: int
    adjusted_close_missing: int
    invalid_timestamps: int
    duplicate_rows: int



class StockHistoryResponse(BaseModel):
    ticker: str
    provider_symbol: str
    market: str
    period: str
    interval: str
    currency: Optional[str] = None

    records: list[StockHistoryRecord]
    record_count: int

    validation: StockHistoryValidation

    data_provider: str
    retrieved_at: datetime


# --------------------------------------------------
# FINANCIAL STATEMENT SCHEMAS
# --------------------------------------------------

class FinancialStatementPeriod(BaseModel):
    period_end: datetime
    values: dict[str, Optional[float]]


class FinancialStatementData(BaseModel):
    statement_type: str
    frequency: str
    periods: list[FinancialStatementPeriod]


class StockFinancialStatementsResponse(BaseModel):
    ticker: str
    provider_symbol: str
    market: str
    currency: Optional[str] = None

    statements: list[FinancialStatementData]

    available_statements: list[str]
    unavailable_statements: list[str]

    data_provider: str
    retrieved_at: datetime
