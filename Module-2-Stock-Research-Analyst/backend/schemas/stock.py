from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ─── 1. Search & Market Schemas ───────────────────────────────────────────────

class MarketStockItem(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None


class MarketInfoResponse(BaseModel):
    code: str
    name: str
    country: str
    country_code: str = "US"
    currency: str
    currency_symbol: str
    suffix: str
    index_name: Optional[str] = None
    index_symbol: Optional[str] = None
    trading_hours: Optional[str] = None
    timezone: Optional[str] = None
    popular_stocks: List[MarketStockItem] = []


class StockSearchResult(BaseModel):
    ticker: str
    company_name: str
    market: str
    exchange: Optional[str] = None
    current_price: Optional[float] = None
    currency: Optional[str] = None
    sector: Optional[str] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None


class StockQuoteResponse(BaseModel):
    ticker: Optional[str] = None
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    pe_ratio: Optional[float] = None
    sector: Optional[str] = None
    currency: Optional[str] = None
    market: Optional[str] = None


# ─── 2. Historical Prices Schemas ────────────────────────────────────────────

class HistoricalPricePoint(BaseModel):
    date: str
    timestamp: int
    close: float
    change: Optional[float] = None
    change_pct: Optional[float] = None


class HistoricalPricesResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    currency: Optional[str] = None
    period: str
    interval: str
    total_points: int
    data_source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    prices: List[HistoricalPricePoint]


# ─── 3. OHLCV Data Schemas ───────────────────────────────────────────────────

class OHLCVBar(BaseModel):
    date: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None

    model_config = {"from_attributes": True}


class OHLCVResponse(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    currency: Optional[str] = None
    period: str
    interval: str
    data_source: str = "Yahoo Finance"
    retrieval_timestamp: datetime
    total_bars: int
    period_open: Optional[float] = None
    period_high: Optional[float] = None
    period_low: Optional[float] = None
    period_close: Optional[float] = None
    net_change: Optional[float] = None
    net_change_pct: Optional[float] = None
    total_volume: Optional[int] = None
    average_volume: Optional[float] = None
    validation_summary: Optional[Dict[str, Any]] = None
    data: List[OHLCVBar]


class CollectOHLCVRequest(BaseModel):
    ticker: str
    period: str = Field(default="1mo", description="Range period, e.g. 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max")
    interval: str = Field(default="1d", description="Bar interval, e.g. 1m, 5m, 15m, 1d, 1wk, 1mo")
    market: Optional[str] = None
    company_name: Optional[str] = None


class CollectOHLCVResponse(BaseModel):
    success: bool
    message: str
    ticker: str
    company_name: Optional[str] = None
    market: Optional[str] = None
    interval: str
    period: str
    bars_collected: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    retrieval_timestamp: datetime
    validation_summary: Optional[Dict[str, Any]] = None
    data: List[OHLCVBar]


# ─── 4. Company Profile & Financial Statements Schemas ───────────────────────

class KeyExecutive(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    pay: Optional[float] = None
    year_born: Optional[int] = None


class CompanyProfileResponse(BaseModel):
    ticker: str
    company_name: str
    market: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    full_time_employees: Optional[int] = None
    description: Optional[str] = None
    key_executives: List[KeyExecutive] = []
    
    # Financial valuation & metrics
    currency: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    dividend_yield: Optional[float] = None
    profit_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    return_on_equity: Optional[float] = None
    revenue_growth: Optional[float] = None
    total_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_debt: Optional[float] = None

    # Provenance tracking
    data_source: str = "Yahoo Finance (Profile & Financials API)"
    retrieval_timestamp: datetime


class IncomeStatementItem(BaseModel):
    date: str
    total_revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    operating_expense: Optional[float] = None
    net_income: Optional[float] = None
    ebitda: Optional[float] = None
    eps: Optional[float] = None


class BalanceSheetItem(BaseModel):
    date: str
    cash_and_equivalents: Optional[float] = None
    short_term_investments: Optional[float] = None
    total_assets: Optional[float] = None
    total_current_liabilities: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_liabilities: Optional[float] = None
    stockholders_equity: Optional[float] = None


class CashFlowStatementItem(BaseModel):
    date: str
    operating_cash_flow: Optional[float] = None
    capital_expenditures: Optional[float] = None
    free_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    net_change_in_cash: Optional[float] = None


class FinancialStatementsResponse(BaseModel):
    ticker: str
    company_name: str
    currency: Optional[str] = None
    market: Optional[str] = None
    income_statements: List[IncomeStatementItem] = []
    balance_sheets: List[BalanceSheetItem] = []
    cash_flows: List[CashFlowStatementItem] = []
    
    # Provenance tracking
    data_source: str = "Yahoo Finance (Financial Statements API)"
    retrieval_timestamp: datetime


# ─── 5. Data Retrieval Audit Log Schema ───────────────────────────────────────

class DataRetrievalAuditLogResponse(BaseModel):
    id: int
    ticker: str
    data_type: str
    data_source: str
    status: str
    record_count: int
    retrieval_timestamp: datetime
    metadata_info: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}

