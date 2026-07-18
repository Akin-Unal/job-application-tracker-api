from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.contact import Contact
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.contact import ContactRead, ContactUpdate
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Contact:
    return ContactService(db).get_for_actor(contact_id, current_user)


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: UUID,
    payload: ContactUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Contact:
    return ContactService(db).update(contact_id, payload, current_user)


@router.delete("/{contact_id}", response_model=MessageResponse)
def delete_contact(
    contact_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    ContactService(db).delete(contact_id, current_user)
    return MessageResponse(message="Contact deleted")
