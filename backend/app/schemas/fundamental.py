"""
fundamental.py – Pydantic schemas for the Fundamental Agent API.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class FundamentalAnalysisRequest(BaseModel):
    """
    Request payload for Fundamental Agent analysis.
    """
    ticker: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Stock ticker symbol (e.g. TCS, AAPL, RELIANCE)",
        examples=["TCS"]
    )
    market: str = Field(
        default="NSE",
        min_length=2,
        max_length=20,
        description="Exchange or market (e.g. NSE, BSE, NASDAQ, NYSE)",
        examples=["NSE"]
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Ticker cannot be empty or whitespace only")
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z0-9.\-_]{1,20}$", cleaned):
            raise ValueError(
                f"Invalid ticker format '{cleaned}'. Ticker must contain only letters, numbers, dots, hyphens, or underscores."
            )
        return cleaned

    @field_validator("market")
    @classmethod
    def validate_market(cls, v: str) -> str:
        if not v or not v.strip():
            return "NSE"
        cleaned = v.strip().upper()
        allowed = {"NSE", "BSE", "NASDAQ", "NYSE"}
        if cleaned not in allowed:
            raise ValueError(
                f"Unsupported market '{cleaned}'. Allowed markets: {', '.join(sorted(allowed))}"
            )
        return cleaned


class FundamentalAnalysisResponse(BaseModel):
    """
    Response schema for Fundamental Agent analysis.
    """
    success: bool
    agent_name: str = "Fundamental Agent"
    ticker: str
    market: str
    company_name: Optional[str] = None
    currency: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_price: Optional[float] = None
    retrieved_at: Optional[str] = None
    data_source: Optional[str] = None
    reporting_periods: Optional[List[str]] = None
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        from_attributes = True
