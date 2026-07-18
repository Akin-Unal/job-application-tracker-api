from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, BaseModel
from app.models.enums import InterviewStatus, InterviewType

if TYPE_CHECKING:
    from app.models.job_application import JobApplication
    from app.models.user import User


class Interview(BaseModel):
    __tablename__ = "interviews"
    __table_args__ = (
        Index("ix_interviews_application_id", "application_id"),
        Index("ix_interviews_scheduled_at", "scheduled_at"),
        Index("ix_interviews_status", "status"),
    )

    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False
    )
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, native_enum=False), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    location_or_link: Mapped[str | None] = mapped_column(String(2048))
    interviewer_name: Mapped[str | None] = mapped_column(String(255))
    interviewer_email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, native_enum=False),
        default=InterviewStatus.SCHEDULED,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    application: Mapped[JobApplication] = relationship(back_populates="interviews")
    created_by: Mapped[User] = relationship(back_populates="interviews")
