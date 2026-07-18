from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application_status_history import ApplicationStatusHistory


class ApplicationStatusHistoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, history: ApplicationStatusHistory) -> None:
        self.db.add(history)

    def list_for_application(self, application_id: UUID) -> list[ApplicationStatusHistory]:
        statement = (
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == application_id)
            .order_by(ApplicationStatusHistory.created_at.asc())
        )
        return list(self.db.scalars(statement))
