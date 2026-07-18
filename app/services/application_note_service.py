from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NoteNotFoundError
from app.models.application_note import ApplicationNote
from app.models.user import User
from app.repositories.application_note_repository import ApplicationNoteRepository
from app.schemas.application_note import (
    ApplicationNoteCreate,
    ApplicationNoteRead,
    ApplicationNoteUpdate,
)
from app.services.application_service import ApplicationService, utc_now


class ApplicationNoteService:
    def __init__(self, db: Session) -> None:
        self.notes = ApplicationNoteRepository(db)
        self.application_service = ApplicationService(db)

    def get_for_actor(self, note_id: UUID, actor: User) -> ApplicationNote:
        note = self.notes.get_with_application(note_id)
        if note is None:
            raise NoteNotFoundError()
        self.application_service._authorize(note.application, actor)
        return note

    def create(
        self, application_id: UUID, payload: ApplicationNoteCreate, actor: User
    ) -> ApplicationNote:
        application = self.application_service.get_for_actor(application_id, actor)
        note = ApplicationNote(
            application_id=application_id,
            author_id=actor.id,
            content=payload.content,
            is_private=payload.is_private,
        )
        application.last_activity_at = utc_now()
        return self.notes.add(note)

    def list_for_application(self, application_id: UUID, actor: User) -> list[ApplicationNoteRead]:
        self.application_service.get_for_actor(application_id, actor)
        return [
            ApplicationNoteRead.model_validate(item)
            for item in self.notes.list_for_application(application_id)
        ]

    def update(self, note_id: UUID, payload: ApplicationNoteUpdate, actor: User) -> ApplicationNote:
        note = self.get_for_actor(note_id, actor)
        values = payload.model_dump(exclude_unset=True)
        for field, value in values.items():
            setattr(note, field, value)
        note.application.last_activity_at = utc_now()
        return self.notes.commit(note)

    def delete(self, note_id: UUID, actor: User) -> None:
        note = self.get_for_actor(note_id, actor)
        note.application.last_activity_at = utc_now()
        self.notes.delete(note)
