from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Registration Schema
class UserRegister(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128
    )


# User Response Schema
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr
    created_at: datetime


# Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# JWT Token Response Schema
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"