from pydantic import BaseModel, EmailStr
from datetime import datetime

# What the user sends us during registration
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# What we return back to the user (hiding the password!)
class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True

 #login   
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ResearchTaskCreate(BaseModel):
    ticker: str
    market: str
    requested_period: str

class WatchlistCreate(BaseModel):
    ticker: str
    market: str = "NASDAQ"

class WatchlistResponse(BaseModel):
    id: int
    ticker: str
    market: str
    added_at: datetime

    class Config:
        from_attributes = True

class UserPreferencesUpdate(BaseModel):
    default_market: str
    default_period: str

class UserPreferencesResponse(BaseModel):
    default_market: str
    default_period: str

    class Config:
        from_attributes = True