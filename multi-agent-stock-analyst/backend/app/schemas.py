from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterSchema(BaseModel):

    full_name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=8, max_length=72)

    confirm_password: str = Field(min_length=8, max_length=72)


class LoginSchema(BaseModel):

    email: EmailStr

    password: str = Field(min_length=1, max_length=72)


class UserResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr