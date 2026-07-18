from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, BaseModel

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.job_application import JobApplication
    from app.models.user import User


class Company(BaseModel):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("created_by_id", "name", name="uq_companies_owner_name"),
        Index("ix_companies_created_by_id", "created_by_id"),
        Index("ix_companies_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048))
    industry: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_by: Mapped[User] = relationship(back_populates="companies")
    contacts: Mapped[list[Contact]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    applications: Mapped[list[JobApplication]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
