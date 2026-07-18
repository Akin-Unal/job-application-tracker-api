from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.application_note import ApplicationNote
from app.repositories.base import BaseRepository


class ApplicationNoteRepository(BaseRepository[ApplicationNote]):
    model = ApplicationNote

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_with_application(self, note_id: UUID) -> ApplicationNote | None:
        return self.db.scalar(
            select(ApplicationNote)
            .options(joinedload(ApplicationNote.application))
            .where(ApplicationNote.id == note_id)
        )

    def list_for_application(self, application_id: UUID) -> list[ApplicationNote]:
        statement = (
            select(ApplicationNote)
            .where(ApplicationNote.application_id == application_id)
            .order_by(ApplicationNote.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def delete(self, note: ApplicationNote) -> None:
        self.db.delete(note)
        self.db.commit()
