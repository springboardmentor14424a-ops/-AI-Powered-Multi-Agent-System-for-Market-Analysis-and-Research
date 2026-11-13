from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]


class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def strip_name(cls, v):
        return v.strip()

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: str
    preferred_market: str
    default_period: str

    model_config = {"from_attributes": True}


class PreferencesIn(BaseModel):
    preferred_market: Market
    default_period: Period


class StockIn(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)

    @field_validator("ticker")
    @classmethod
    def clean(cls, v):
        v = v.strip().upper()
        if not v.replace(".", "").replace("-", "").replace("&", "").isalnum():
            raise ValueError("Ticker can only contain letters, numbers, . - &")
        return v


class SavedStockOut(BaseModel):
    saved_stock_id: int
    ticker: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResearchTaskOut(BaseModel):
    task_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskIn(BaseModel):
    ticker: str = Field(min_length=1, max_length=20)
    market: Market
    period: Period

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v):
        v = v.strip().upper()
        if not v.replace(".", "").replace("-", "").replace("&", "").isalnum():
            raise ValueError("Ticker can only contain letters, numbers, . - &")
        return v
