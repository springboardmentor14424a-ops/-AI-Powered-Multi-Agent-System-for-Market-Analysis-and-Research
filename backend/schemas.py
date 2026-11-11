
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------
# COMMON VALIDATION TYPES
# ---------------------------------------------------------

MarketType = Literal["NSE", "BSE", "US"]

PeriodType = Literal[
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max"
]

TaskStatus = Literal[
    "PENDING",
    "PROCESSING",
    "COMPLETED",
    "FAILED"
]


# ---------------------------------------------------------
# 1. USER REGISTRATION
# ---------------------------------------------------------

class UserRegister(BaseModel):

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=150
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )

    confirm_password: str = Field(
        ...,
        min_length=8,
        max_length=72
    )


# ---------------------------------------------------------
# 2. USER LOGIN
# ---------------------------------------------------------

class UserLogin(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=1
    )


# ---------------------------------------------------------
# 3. AUTHENTICATION RESPONSE
# ---------------------------------------------------------

class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"


# ---------------------------------------------------------
# 4. USER PREFERENCES
# ---------------------------------------------------------

class PreferenceUpdate(BaseModel):

    preferred_market: MarketType

    default_period: PeriodType


class PreferenceResponse(BaseModel):

    pref_id: int

    user_id: int

    preferred_market: MarketType

    default_period: PeriodType

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 5. WATCHLIST
# ---------------------------------------------------------

class WatchlistAdd(BaseModel):

    ticker: str = Field(
        ...,
        min_length=1,
        max_length=30,
        pattern=r"^[A-Za-z0-9^.=_-]+$"
    )


class WatchlistResponse(BaseModel):

    saved_stock_id: int

    ticker: str

    user_id: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 6. RESEARCH HISTORY
# ---------------------------------------------------------

class ResearchTaskResponse(BaseModel):

    task_id: int

    user_id: int

    ticker: str

    market: MarketType

    requested_period: PeriodType

    status: TaskStatus

    created_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 7. HISTORICAL STOCK DATA
# ---------------------------------------------------------

class HistoricalDataPoint(BaseModel):

    date: str

    open: float

    high: float

    low: float

    close: float

    volume: int


# ---------------------------------------------------------
# 8. STOCK SEARCH RESPONSE
# ---------------------------------------------------------

class StockSearchResponse(BaseModel):

    task_id: int

    ticker: str

    company_name: str

    market: MarketType

    period: PeriodType

    historical_data: list[HistoricalDataPoint]


# ---------------------------------------------------------
# 9. AGENT RESULT
# ---------------------------------------------------------

class AgentResultResponse(BaseModel):

    result_id: int

    task_id: int

    agent_type: str

    status: str

    summary: Optional[str] = None

    result_data: Optional[dict[str, Any]] = None

    error_message: Optional[str] = None

    started_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 10. SOURCE DOCUMENT
# ---------------------------------------------------------

class SourceDocumentResponse(BaseModel):

    source_id: int

    task_id: int

    source_type: str

    title: str

    url: Optional[str] = None

    publisher: Optional[str] = None

    published_at: Optional[datetime] = None

    retrieved_at: datetime

    content_summary: Optional[str] = None

    metadata_json: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 11. RESEARCH REPORT
# ---------------------------------------------------------

class ResearchReportResponse(BaseModel):

    report_id: int

    task_id: int

    title: str

    executive_summary: Optional[str] = None

    report_data: Optional[dict[str, Any]] = None

    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# 12. GENERAL API MESSAGE
# ---------------------------------------------------------

class MessageResponse(BaseModel):

    message: str
