from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RatioInputForm(BaseModel):
    price: Optional[float] = Field(None, description="Current share price", ge=0)
    net_income: Optional[float] = Field(None, description="Net income")
    shares_outstanding: Optional[float] = Field(None, description="Shares outstanding", gt=0)
    total_shareholder_equity: Optional[float] = Field(None, description="Total shareholder equity")
    total_debt: Optional[float] = Field(None, description="Total debt", ge=0)
    current_assets: Optional[float] = Field(None, description="Current assets", ge=0)
    current_liabilities: Optional[float] = Field(None, description="Current liabilities", ge=0)
    total_revenue: Optional[float] = Field(None, description="Total revenue", gt=0)
    total_assets: Optional[float] = Field(None, description="Total assets", gt=0)
    eps: Optional[float] = Field(None, description="Direct EPS override if available")


class RatioMetricDetail(BaseModel):
    value: Optional[float] = None
    display: str
    description: str


class StockFinancialRatiosResponse(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    currency: Optional[str] = "USD"
    price: Optional[float] = None
    financial_ratios: Dict[str, RatioMetricDetail]
    raw_financials: Optional[Dict[str, Optional[float]]] = None
