from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


AnalysisPeriod = Literal["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
MarketCode = Literal["US", "NSE", "BSE"]


class UserPreferenceUpdate(BaseModel):
    market: MarketCode = "US"
    analysis_period: AnalysisPeriod = "1y"


class UserPreferenceResponse(UserPreferenceUpdate):
    model_config = ConfigDict(from_attributes=True)

    updated_at: datetime


class StockSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: str | None = None
    quote_type: str | None = None


class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]
    market: MarketCode
    source: str
    retrieved_at: datetime


class DataSourceInfo(BaseModel):
    provider: str
    url: str
    retrieved_at: datetime


class OHLCVBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int | None = None


class MarketDataResponse(BaseModel):
    ticker: str
    market: MarketCode
    company_name: str
    currency: str | None = None
    exchange: str | None = None
    period: str
    prices: list[OHLCVBar]
    warnings: list[str]
    source: DataSourceInfo


class FundamentalAnalysisRequest(BaseModel):
    ticker: str = Field(pattern=r"^[A-Za-z0-9.^=&_-]{1,30}$")
    period: AnalysisPeriod = "1y"
    market: MarketCode = "US"

    @model_validator(mode="after")
    def normalize_ticker(self) -> "FundamentalAnalysisRequest":
        self.ticker = self.ticker.upper()
        return self


class FundamentalMetrics(BaseModel):
    market_cap: float | None = None
    current_price: float | None = None
    trailing_pe: float | None = None
    price_to_book: float | None = None
    return_on_equity_percent: float | None = None
    profit_margin_percent: float | None = None
    operating_margin_percent: float | None = None
    debt_to_equity_percent: float | None = None
    net_debt: float | None = None
    current_ratio: float | None = None
    revenue_growth_percent: float | None = None
    net_income_growth_percent: float | None = None


class FinancialPeriod(BaseModel):
    period: str
    revenue: float | None = None
    net_income: float | None = None
    total_debt: float | None = None
    cash: float | None = None
    shareholders_equity: float | None = None


class PeerComparison(BaseModel):
    ticker: str
    company_name: str
    trailing_pe: float | None = None
    price_to_book: float | None = None
    return_on_equity_percent: float | None = None
    profit_margin_percent: float | None = None
    debt_to_equity_percent: float | None = None


class FundamentalAnalysisResponse(BaseModel):
    ticker: str
    market: MarketCode
    company_name: str
    sector: str | None = None
    industry: str | None = None
    currency: str | None = None
    exchange: str | None = None
    metrics: FundamentalMetrics
    historical_financials: list[FinancialPeriod]
    peer_comparisons: list[PeerComparison]
    findings: list[str]
    data_gaps: list[str]
    market_data: MarketDataResponse
    source: DataSourceInfo


class SavedStockCreate(BaseModel):
    ticker: str = Field(pattern=r"^[A-Za-z0-9.^=&_-]{1,30}$")
    market: MarketCode = "US"
    watchlist_name: str = Field(default="My Watchlist", min_length=1, max_length=60)

    @model_validator(mode="after")
    def normalize_fields(self) -> "SavedStockCreate":
        self.ticker = self.ticker.strip().upper()
        self.watchlist_name = self.watchlist_name.strip()
        return self


class SavedStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved_stock_id: int
    ticker: str
    market: MarketCode
    watchlist_name: str
    created_at: datetime


class ResearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    ticker: str
    market: MarketCode
    requested_period: AnalysisPeriod
    status: str
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ResearchReportResponse(ResearchHistoryItem):
    result: dict[str, Any] | None = None


class RegistrationRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "RegistrationRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str = Field(min_length=20, max_length=8192)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
