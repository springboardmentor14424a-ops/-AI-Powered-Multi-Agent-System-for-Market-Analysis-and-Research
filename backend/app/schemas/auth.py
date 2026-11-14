
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Full name must contain at least 2 characters")
        return value

    @field_validator("confirm_password")
    @classmethod
    def validate_confirmation(cls, value, info):
        password = info.data.get("password")
        if password and value != password:
            raise ValueError("Passwords do not match")
        return value
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        import re

        if len(value) < 8:
            raise ValueError("Password must contain at least 8 characters")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain at least one special character")

        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 bytes")

        return value



class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class GoogleLogin(BaseModel):
    id_token: str = Field(min_length=1)