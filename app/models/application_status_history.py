from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base
from app.models.enums import ApplicationStatus

if TYPE_CHECKING:
    from app.models.job_application import JobApplication
    from app.models.user import User


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    __table_args__ = (Index("ix_application_status_history_application_id", "application_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False
    )
    changed_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    old_status: Mapped[ApplicationStatus | None] = mapped_column(
        Enum(ApplicationStatus, native_enum=False)
    )
    new_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, native_enum=False), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped[JobApplication] = relationship(back_populates="status_history")
    changed_by: Mapped[User] = relationship(back_populates="status_history_records")
