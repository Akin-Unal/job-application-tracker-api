from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import InterviewStatus, InterviewType


class InterviewCreate(BaseModel):
    interview_type: InterviewType = Field(examples=[InterviewType.TECHNICAL])
    scheduled_at: datetime
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    location_or_link: str | None = Field(default=None, max_length=2048)
    interviewer_name: str | None = Field(default=None, max_length=255)
    interviewer_email: EmailStr | None = None
    status: InterviewStatus = InterviewStatus.SCHEDULED
    notes: str | None = None


class InterviewUpdate(BaseModel):
    interview_type: InterviewType | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    location_or_link: str | None = Field(default=None, max_length=2048)
    interviewer_name: str | None = Field(default=None, max_length=255)
    interviewer_email: EmailStr | None = None
    status: InterviewStatus | None = None
    notes: str | None = None


class InterviewRead(BaseModel):
    id: UUID
    application_id: UUID
    interview_type: InterviewType
    scheduled_at: datetime
    duration_minutes: int
    location_or_link: str | None
    interviewer_name: str | None
    interviewer_email: str | None
    status: InterviewStatus
    notes: str | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
