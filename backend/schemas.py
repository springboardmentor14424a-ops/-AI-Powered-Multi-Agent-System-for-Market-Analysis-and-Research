from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class PreferenceUpdate(BaseModel):
    preferred_market: str
    default_period: str

class WatchlistAdd(BaseModel):
    ticker: str
