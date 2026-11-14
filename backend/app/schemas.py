import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        # bcrypt only uses the first 72 bytes, so reject anything longer.
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes long.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include a lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include an uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must include a number.")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match.")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return str(v).strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime


class RegisterOut(BaseModel):
    message: str
    user: UserOut


class SessionOut(BaseModel):
    user: UserOut
    # Sent in the X-CSRF-Token header on state-changing requests.
    csrf_token: str | None = None


class LoginOut(SessionOut):
    message: str


# ---------- research history ----------

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
AnalysisPeriod = Literal["1 month", "3 months", "6 months", "1 year", "5 years"]
Status = Literal["pending", "processing", "completed", "failed"]

# Ticker format each market's data provider expects (as stored in this app).
_TICKER_FORMATS = {
    "NSE": (r"[A-Z0-9&\-]{1,12}", "NSE symbols are letters/numbers, e.g. RELIANCE or TCS."),
    "BSE": (r"\d{6}", "BSE tickers are 6-digit scrip codes, e.g. 500325."),
    "NASDAQ": (r"[A-Z]{1,5}([.\-][A-Z]{1,2})?", "US tickers are 1-5 letters, e.g. AAPL."),
    "NYSE": (r"[A-Z]{1,5}([.\-][A-Z]{1,2})?", "US tickers are 1-5 letters, e.g. JPM."),
}


def normalise_ticker(market: str | None, value: str) -> str:
    """Uppercase, trim, drop a pasted provider suffix, and check the market's format."""
    v = value.strip().upper()
    if market == "NSE" and v.endswith(".NS"):
        v = v[:-3]
    if market == "BSE" and v.endswith(".BO"):
        v = v[:-3]
    if market in _TICKER_FORMATS:
        pattern, hint = _TICKER_FORMATS[market]
        if not re.fullmatch(pattern, v):
            raise ValueError(hint)
    elif not re.fullmatch(r"[A-Z0-9.&\-]{1,12}", v):
        raise ValueError("Enter a valid ticker symbol.")
    return v


class ResearchIn(BaseModel):
    """Deliberately has NO user_id: the owner always comes from the verified JWT."""

    # `market` comes first so the ticker validator can check the market's format.
    market: Market
    company_name: str = Field(min_length=2, max_length=100)
    ticker: str
    analysis_period: AnalysisPeriod

    @field_validator("company_name")
    @classmethod
    def clean_company(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Enter the company name.")
        return v

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str, info) -> str:
        return normalise_ticker(info.data.get("market"), v)


class ResearchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    ticker: str
    market: str
    analysis_period: str
    status: Status
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ResearchDetail(ResearchSummary):
    report: str | None = None


# ---------- stock search, watchlist, preferences ----------

class StockOut(BaseModel):
    ticker: str
    company_name: str
    market: Market
    provider_symbol: str


class WatchlistIn(BaseModel):
    """Only the listing to save. The owner comes from the JWT; the company name
    is looked up server-side, never trusted from the browser."""

    market: Market
    ticker: str

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str, info) -> str:
        return normalise_ticker(info.data.get("market"), v)


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    company_name: str
    market: Market
    created_at: datetime


class PreferencesIn(BaseModel):
    market: Market
    analysis_period: AnalysisPeriod


class PreferencesOut(PreferencesIn):
    pass
