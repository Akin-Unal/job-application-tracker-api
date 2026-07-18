from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserRead


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(min_length=8, examples=["StrongPassword123"])


class RegisterRequest(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["StrongPassword123"])
    full_name: str = Field(min_length=1, max_length=255, examples=["Example User"])


class AuthUserResponse(UserRead):
    pass
