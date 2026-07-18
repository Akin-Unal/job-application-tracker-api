from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr = Field(examples=["user@example.com"])
    full_name: str = Field(min_length=1, max_length=255, examples=["Example User"])


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128, examples=["StrongPassword123"])
    role: UserRole = UserRole.USER


class UserRead(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
