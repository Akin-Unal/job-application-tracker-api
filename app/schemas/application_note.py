from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NoteContentMixin(BaseModel):
    content: str = Field(min_length=1, examples=["Follow up with the recruiter on Friday"])

    @field_validator("content")
    @classmethod
    def trim_and_validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value


class ApplicationNoteCreate(NoteContentMixin):
    is_private: bool = True


class ApplicationNoteUpdate(BaseModel):
    content: str | None = None
    is_private: bool | None = None

    @field_validator("content")
    @classmethod
    def trim_and_validate_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("content must not be empty")
        return value


class ApplicationNoteRead(BaseModel):
    id: UUID
    application_id: UUID
    author_id: UUID
    content: str
    is_private: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
