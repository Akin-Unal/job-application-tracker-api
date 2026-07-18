from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.application_note import ApplicationNote
from app.models.user import User
from app.schemas.application_note import ApplicationNoteRead, ApplicationNoteUpdate
from app.schemas.common import MessageResponse
from app.services.application_note_service import ApplicationNoteService

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.patch("/{note_id}", response_model=ApplicationNoteRead)
def update_note(
    note_id: UUID,
    payload: ApplicationNoteUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApplicationNote:
    return ApplicationNoteService(db).update(note_id, payload, current_user)


@router.delete("/{note_id}", response_model=MessageResponse)
def delete_note(
    note_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    ApplicationNoteService(db).delete(note_id, current_user)
    return MessageResponse(message="Application note deleted")
