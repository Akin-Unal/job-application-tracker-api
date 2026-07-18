from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.models.enums import (
    ApplicationPriority,
    ApplicationSource,
    ApplicationStatus,
    EmploymentType,
    WorkMode,
)


class ApplicationCreate(BaseModel):
    company_id: UUID
    position_title: str = Field(min_length=1, max_length=180, examples=["Backend Engineer"])
    job_url: HttpUrl | None = Field(default=None, examples=["https://example.com/jobs/123"])
    location: str | None = Field(default=None, max_length=255)
    work_mode: WorkMode = WorkMode.UNSPECIFIED
    employment_type: EmploymentType = EmploymentType.UNSPECIFIED
    source: ApplicationSource = ApplicationSource.OTHER
    status: ApplicationStatus = ApplicationStatus.DRAFT
    priority: ApplicationPriority = ApplicationPriority.MEDIUM
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10, examples=["USD"])
    applied_at: datetime | None = None
    deadline_at: datetime | None = None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "ApplicationCreate":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min must not be greater than salary_max")
        return self


class ApplicationUpdate(BaseModel):
    company_id: UUID | None = None
    position_title: str | None = Field(default=None, min_length=1, max_length=180)
    job_url: HttpUrl | None = None
    location: str | None = Field(default=None, max_length=255)
    work_mode: WorkMode | None = None
    employment_type: EmploymentType | None = None
    source: ApplicationSource | None = None
    status: ApplicationStatus | None = None
    priority: ApplicationPriority | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    applied_at: datetime | None = None
    deadline_at: datetime | None = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus = Field(examples=[ApplicationStatus.APPLIED])
    note: str | None = Field(default=None, examples=["Application submitted via careers page"])


class ApplicationArchiveRequest(BaseModel):
    note: str | None = Field(default=None, examples=["Closed after receiving final response"])


class CompanySummary(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class ApplicationRead(BaseModel):
    id: UUID
    company_id: UUID
    company: CompanySummary
    position_title: str
    job_url: str | None
    location: str | None
    work_mode: WorkMode
    employment_type: EmploymentType
    source: ApplicationSource
    status: ApplicationStatus
    priority: ApplicationPriority
    salary_min: int | None
    salary_max: int | None
    currency: str | None
    applied_at: datetime | None
    deadline_at: datetime | None
    last_activity_at: datetime | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ApplicationStatistics(BaseModel):
    total_applications: int
    draft: int
    applied: int
    hr_screen: int
    technical_interview: int
    final_interview: int
    offer: int
    rejected: int
    withdrawn: int
    archived: int
    upcoming_interviews: int
    applications_this_week: int
    applications_this_month: int
    response_rate_percent: float
    offer_rate_percent: float
