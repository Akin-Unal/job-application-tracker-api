from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApplicationStatus


class ApplicationStatusHistoryRead(BaseModel):
    id: UUID
    application_id: UUID
    changed_by_id: UUID
    old_status: ApplicationStatus | None
    new_status: ApplicationStatus
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
