import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator[uuid.UUID]):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(
        self, value: uuid.UUID | str | None, dialect: Any
    ) -> str | uuid.UUID | None:
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))

    def process_result_value(self, value: uuid.UUID | str | None, _: Any) -> uuid.UUID | None:
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


Str50 = String(50)
