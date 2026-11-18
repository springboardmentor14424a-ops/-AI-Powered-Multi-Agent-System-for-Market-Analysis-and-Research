from datetime import datetime
from typing import Optional, List
import re
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email_str(value: str) -> str:
    cleaned = value.strip().lower()
    if not EMAIL_REGEX.match(cleaned):
        raise ValueError("Invalid email format. Please provide a valid email address.")
    return cleaned

# User Schemas
class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)

class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str

    @field_validator("email")
    @classmethod
    def check_email(cls, v: str) -> str:
        return validate_email_str(v)

class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[int] = None

# Watchlist (Saved Stocks) Schemas
class SavedStockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)

class SavedStockResponse(BaseModel):
    saved_stock_id: int
    user_id: int
    ticker: str
    created_at: datetime

    class Config:
        from_attributes = True

# Research Task Schemas
class ResearchTaskCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    market: str = Field("NSE", pattern="^(NSE|BSE|NASDAQ|NYSE)$")
    requested_period: str = Field("6 Months", pattern="^(1 Month|3 Months|6 Months|1 Year|5 Years)$")

class ResearchTaskResponse(BaseModel):
    task_id: int
    user_id: int
    ticker: str
    company_name: Optional[str] = None
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    target_price: Optional[str] = None
    report_json: Optional[str] = None

    class Config:
        from_attributes = True

# Extended Multi-Agent Report Schemas
class ResearchReportResponse(BaseModel):
    report_id: int
    task_id: int
    consolidated_report: str
    summary: str
    limitations: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AgentResultResponse(BaseModel):
    result_id: int
    task_id: int
    agent_name: str
    status: str
    structured_output: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SourceDocumentResponse(BaseModel):
    document_id: int
    task_id: int
    source_title: str
    url: str
    publication_time: datetime
    retrieval_time: datetime

    class Config:
        from_attributes = True

# Preferences Schemas
class UserPreferenceUpdate(BaseModel):
    preferred_market: str = Field(..., pattern="^(NSE|BSE|NASDAQ|NYSE)$")
    preferred_analysis_period: str = Field(..., pattern="^(1 Month|3 Months|6 Months|1 Year|5 Years)$")

class UserPreferenceResponse(BaseModel):
    preferred_market: str
    preferred_analysis_period: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================================================
# MODULE 2: STOCK SEARCH & MARKET DATA COLLECTION SCHEMAS
# =========================================================

class CompanySearchResult(BaseModel):
    ticker: str
    name: str
    market: str
    sector: Optional[str] = None
    currency: Optional[str] = "USD"
    base_price: Optional[float] = None
    country: Optional[str] = None

class OHLCVPoint(BaseModel):
    date: str
    display_date: Optional[str] = None
    open: float
    high: float
    low: float
    close: float
    volume: int

class ValidationReport(BaseModel):
    is_valid: bool
    quality_score: float
    total_records: int
    clean_records: int
    missing_values_handled: int
    duplicate_dates_removed: int
    inconsistencies_corrected: int
    issues_log: List[str]
    validated_at: str

class HistoricalOHLCVResponse(BaseModel):
    ticker: str
    market: str
    period: str
    interval: str
    currency: str
    current_price: float
    data_source: str
    retrieval_timestamp: str
    points: List[OHLCVPoint]
    validation: ValidationReport

class CompanyProfileResponse(BaseModel):
    ticker: str
    name: str
    market: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    ceo: Optional[str] = None
    employees: Optional[int] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    market_cap: Optional[str] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    currency: str = "USD"
    data_source: str
    retrieval_timestamp: str

class FinancialStatementsResponse(BaseModel):
    ticker: str
    market: str
    period_type: str  # annual or quarterly
    currency: str
    data_source: str
    retrieval_timestamp: str
    income_statement: List[dict]
    balance_sheet: List[dict]
    cash_flow: List[dict]
    ratios: dict

class RawDataValidationRequest(BaseModel):
    ticker: str
    market: str = "NSE"
    records: List[dict]

class RawDataValidationResponse(BaseModel):
    ticker: str
    market: str
    data_source: str
    clean_records: List[OHLCVPoint]
    validation_report: ValidationReport

class MarketProviderStatus(BaseModel):
    alpha_vantage_configured: bool
    alpha_vantage_masked_key: Optional[str] = None
    twelve_data_configured: bool
    twelve_data_masked_key: Optional[str] = None
    active_providers: List[str]
    supported_markets: List[str]
    cache_engine: str

class ProviderKeyUpdate(BaseModel):
    alpha_vantage_key: Optional[str] = None
    twelve_data_key: Optional[str] = None

