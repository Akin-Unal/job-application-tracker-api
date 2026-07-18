from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160, examples=["Acme Technologies"])
    website_url: HttpUrl | None = Field(default=None, examples=["https://example.com"])
    industry: str | None = Field(default=None, max_length=160, examples=["Software"])
    location: str | None = Field(default=None, max_length=255, examples=["Istanbul, Türkiye"])
    notes: str | None = Field(default=None, examples=["Product-led SaaS company"])


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    website_url: HttpUrl | None = None
    industry: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class CompanyRead(BaseModel):
    id: UUID
    name: str
    website_url: str | None
    industry: str | None
    location: str | None
    notes: str | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
