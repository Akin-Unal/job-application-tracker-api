from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, BaseModel
from app.models.enums import (
    ApplicationPriority,
    ApplicationSource,
    ApplicationStatus,
    EmploymentType,
    WorkMode,
)

if TYPE_CHECKING:
    from app.models.application_note import ApplicationNote
    from app.models.application_status_history import ApplicationStatusHistory
    from app.models.company import Company
    from app.models.interview import Interview
    from app.models.user import User


class JobApplication(BaseModel):
    __tablename__ = "job_applications"
    __table_args__ = (
        Index("ix_job_applications_company_id", "company_id"),
        Index("ix_job_applications_created_by_id", "created_by_id"),
        Index("ix_job_applications_status", "status"),
        Index("ix_job_applications_priority", "priority"),
        Index("ix_job_applications_source", "source"),
        Index("ix_job_applications_work_mode", "work_mode"),
        Index("ix_job_applications_employment_type", "employment_type"),
        Index("ix_job_applications_applied_at", "applied_at"),
        Index("ix_job_applications_deadline_at", "deadline_at"),
        Index("ix_job_applications_created_at", "created_at"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    position_title: Mapped[str] = mapped_column(String(180), nullable=False)
    job_url: Mapped[str | None] = mapped_column(String(2048))
    location: Mapped[str | None] = mapped_column(String(255))
    work_mode: Mapped[WorkMode] = mapped_column(
        Enum(WorkMode, native_enum=False), default=WorkMode.UNSPECIFIED, nullable=False
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, native_enum=False),
        default=EmploymentType.UNSPECIFIED,
        nullable=False,
    )
    source: Mapped[ApplicationSource] = mapped_column(
        Enum(ApplicationSource, native_enum=False),
        default=ApplicationSource.OTHER,
        nullable=False,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False),
        default=ApplicationStatus.DRAFT,
        nullable=False,
    )
    priority: Mapped[ApplicationPriority] = mapped_column(
        Enum(ApplicationPriority, native_enum=False),
        default=ApplicationPriority.MEDIUM,
        nullable=False,
    )
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str | None] = mapped_column(String(10))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship(back_populates="applications")
    created_by: Mapped[User] = relationship(back_populates="applications")
    status_history: Mapped[list[ApplicationStatusHistory]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.created_at",
    )
    interviews: Mapped[list[Interview]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    notes: Mapped[list[ApplicationNote]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
