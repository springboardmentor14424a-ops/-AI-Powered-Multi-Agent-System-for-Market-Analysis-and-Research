from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
import re


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_symbol(v: str) -> str:
    cleaned = v.strip().upper()
    if not cleaned:
        raise ValueError("Stock symbol cannot be empty.")
    if not re.match(r"^[A-Z0-9\.\-\^]+$", cleaned):
        raise ValueError(f"Invalid stock symbol format: '{cleaned}'.")
    return cleaned


class AgentSymbolQuery(BaseModel):
    symbol: str = Field(..., description="Stock ticker symbol (e.g., AAPL, MSFT, TSLA)")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        return _normalize_symbol(v)


# =====================================================================
# 1. Fundamental Analysis Schemas
# =====================================================================

class FundamentalRatios(BaseModel):
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    net_profit_margin: Optional[float] = None
    roa: Optional[float] = None


class FundamentalAnalysisResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    total_debt: Optional[float] = None
    ratios: FundamentalRatios
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    financial_health_score: float = Field(..., ge=0, le=100)
    financial_health_summary: str
    ai_generated_report: str
    timestamp: str = Field(default_factory=_utcnow_iso)


# =====================================================================
# 2. Technical Analysis Schemas
# =====================================================================

class TechnicalIndicatorsSummary(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    ema_50: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    indicators: TechnicalIndicatorsSummary
    bullish_signals: List[str] = Field(default_factory=list)
    bearish_signals: List[str] = Field(default_factory=list)
    neutral_signals: List[str] = Field(default_factory=list)
    overall_signal: str  # "Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"
    signal_score: float = Field(..., ge=-100, le=100)  # -100 (Extremely Bearish) to +100 (Extremely Bullish)
    summary: str
    chart_json: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=_utcnow_iso)


# =====================================================================
# 3. News & Sentiment Schemas
# =====================================================================

class NewsArticle(BaseModel):
    headline: str
    description: Optional[str] = None
    source: str
    published_at: str
    url: str
    sentiment: str  # "Positive", "Negative", "Neutral"
    sentiment_score: float  # -1.0 to 1.0
    summary: Optional[str] = None


class NewsSentimentResponse(BaseModel):
    symbol: str
    articles: List[NewsArticle] = Field(default_factory=list)
    overall_sentiment: str  # "Positive", "Negative", "Neutral"
    overall_score: float  # -1.0 to 1.0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    executive_summary: str
    timestamp: str = Field(default_factory=_utcnow_iso)


# =====================================================================
# 4. Risk Analysis Schemas
# =====================================================================

class RiskAnalysisResponse(BaseModel):
    symbol: str
    volatility_annualized: float = Field(..., description="Annualized volatility in percentage (e.g. 25.4%)")
    beta: Optional[float] = Field(None, description="Beta relative to S&P 500 (SPY)")
    max_drawdown: float = Field(..., description="Maximum peak-to-trough drop in percentage (e.g. -18.2%)")
    standard_deviation_daily: float = Field(..., description="Daily return standard deviation in percentage")
    standard_deviation_annualized: float = Field(..., description="Annualized standard deviation in percentage")
    risk_score: float = Field(..., ge=0, le=100, description="Composite risk score from 0 (very safe) to 100 (extreme risk)")
    risk_level: str  # "Low", "Moderate", "High"
    market_risks: List[str] = Field(default_factory=list)
    summary: str
    timestamp: str = Field(default_factory=_utcnow_iso)


# =====================================================================
# 5. Combined Multi-Agent Synthesis Schema
# =====================================================================

class MultiAgentSummaryResponse(BaseModel):
    symbol: str
    fundamental: FundamentalAnalysisResponse
    technical: TechnicalAnalysisResponse
    news_sentiment: NewsSentimentResponse
    risk: RiskAnalysisResponse
    composite_verdict: str  # e.g., "Bullish Outperform", "Cautious Hold", etc.
    composite_score: float  # 0 to 100
    executive_summary: str
    timestamp: str = Field(default_factory=_utcnow_iso)
