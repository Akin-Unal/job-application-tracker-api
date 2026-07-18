from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class ContactCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255, examples=["Alex Recruiter"])
    email: EmailStr | None = Field(default=None, examples=["alex@example.com"])
    phone: str | None = Field(default=None, max_length=50)
    role: str | None = Field(default=None, max_length=160, examples=["Technical Recruiter"])
    linkedin_url: HttpUrl | None = None
    notes: str | None = None


class ContactUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    role: str | None = Field(default=None, max_length=160)
    linkedin_url: HttpUrl | None = None
    notes: str | None = None


class ContactRead(BaseModel):
    id: UUID
    company_id: UUID
    full_name: str
    email: str | None
    phone: str | None
    role: str | None
    linkedin_url: str | None
    notes: str | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
