from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.application_note import ApplicationNote
    from app.models.application_status_history import ApplicationStatusHistory
    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.interview import Interview
    from app.models.job_application import JobApplication


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    companies: Mapped[list[Company]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )
    contacts: Mapped[list[Contact]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )
    applications: Mapped[list[JobApplication]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )
    interviews: Mapped[list[Interview]] = relationship(
        back_populates="created_by", cascade="all, delete-orphan"
    )
    application_notes: Mapped[list[ApplicationNote]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )
    status_history_records: Mapped[list[ApplicationStatusHistory]] = relationship(
        back_populates="changed_by", cascade="all, delete-orphan"
    )
