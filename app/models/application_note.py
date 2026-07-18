from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.job_application import JobApplication
    from app.models.user import User


class ApplicationNote(BaseModel):
    __tablename__ = "application_notes"
    __table_args__ = (Index("ix_application_notes_application_id", "application_id"),)

    application_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    application: Mapped[JobApplication] = relationship(back_populates="notes")
    author: Mapped[User] = relationship(back_populates="application_notes")
