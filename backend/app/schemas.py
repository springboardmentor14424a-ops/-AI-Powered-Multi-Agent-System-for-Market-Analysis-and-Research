import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

Market = Literal["NSE", "BSE", "NASDAQ", "NYSE"]
Period = Literal["1M", "3M", "6M", "1Y", "5Y"]


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SavedStockCreate(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.\-&^]{1,20}", v):
            raise ValueError("Invalid ticker symbol")
        return v


class SavedStockOut(BaseModel):
    saved_stock_id: int
    ticker: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PreferencesIn(BaseModel):
    market: Market
    default_period: Period


class PreferencesOut(BaseModel):
    market: Market
    default_period: Period

    model_config = {"from_attributes": True}

 class ResearchCreate(BaseModel):
    ticker: str
    market: Market | None = None
    requested_period: Period | None = None

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z0-9.\-&^]{1,20}", v):
            raise ValueError("Invalid ticker symbol")
        return v


class ResearchTaskOut(BaseModel):
    task_id: int
    ticker: str
    market: str
    requested_period: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}  