from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
AnalysisPeriod = Literal["1M", "3M", "6M", "1Y", "5Y"]


def _check_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes long")
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one letter and one number")
    return value


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return _check_password_strength(v)

    @model_validator(mode="after")
    def _passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def _lower_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime


class LoginResponse(BaseModel):
    user: UserOut
    csrf_token: str


# ---------- Preferences ----------
class PreferencesIn(BaseModel):
    market: Market
    analysis_period: AnalysisPeriod


class PreferencesOut(PreferencesIn):
    model_config = ConfigDict(from_attributes=True)


# ---------- Stocks / watchlist ----------
class StockOut(BaseModel):
    ticker: str
    name: str
    market: Market
    provider_symbol: str
    source: str = "catalog"  # "yahoo" or "catalog"


class WatchlistAdd(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class SavedStockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    saved_stock_id: int
    ticker: str
    company_name: str
    market: Market
    created_at: datetime


# ---------- Research ----------
class ResearchCreate(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market | None = None  # falls back to the user's saved preference
    analysis_period: AnalysisPeriod | None = None  # falls back to the saved preference

    @field_validator("ticker")
    @classmethod
    def _upper(cls, v: str) -> str:
        return v.strip().upper()


class ResearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    task_id: int
    ticker: str
    company_name: str
    market: Market
    analysis_period: AnalysisPeriod
    status: str
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ResearchDetailOut(ResearchOut):
    report: str | None = None
