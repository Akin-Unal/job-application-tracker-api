from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ContactNotFoundError
from app.models.contact import Contact
from app.models.user import User
from app.repositories.contact_repository import ContactRepository
from app.schemas.common import PaginatedResponse
from app.schemas.contact import ContactCreate, ContactRead, ContactUpdate
from app.services.company_service import CompanyService
from app.utils.pagination import PaginationParams, total_pages


class ContactService:
    def __init__(self, db: Session) -> None:
        self.contacts = ContactRepository(db)
        self.company_service = CompanyService(db)

    def get_for_actor(self, contact_id: UUID, actor: User) -> Contact:
        contact = self.contacts.get_with_company(contact_id)
        if contact is None:
            raise ContactNotFoundError()
        self.company_service._authorize(contact.company, actor)
        return contact

    def create(self, company_id: UUID, payload: ContactCreate, actor: User) -> Contact:
        self.company_service.get_for_actor(company_id, actor)
        values = payload.model_dump()
        if values.get("linkedin_url") is not None:
            values["linkedin_url"] = str(values["linkedin_url"])
        if values.get("email") is not None:
            values["email"] = str(values["email"])
        contact = Contact(
            company_id=company_id,
            created_by_id=actor.id,
            **values,
        )
        return self.contacts.add(contact)

    def list_for_company(
        self, company_id: UUID, params: PaginationParams, actor: User
    ) -> PaginatedResponse[ContactRead]:
        self.company_service.get_for_actor(company_id, actor)
        contacts, total = self.contacts.list_for_company(
            company_id, params.offset, params.page_size
        )
        return PaginatedResponse[ContactRead](
            items=[ContactRead.model_validate(item) for item in contacts],
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages(total, params.page_size),
        )

    def update(self, contact_id: UUID, payload: ContactUpdate, actor: User) -> Contact:
        contact = self.get_for_actor(contact_id, actor)
        values = payload.model_dump(exclude_unset=True)
        for url_field in ("linkedin_url", "email"):
            if values.get(url_field) is not None:
                values[url_field] = str(values[url_field])
        for field, value in values.items():
            setattr(contact, field, value)
        return self.contacts.commit(contact)

    def delete(self, contact_id: UUID, actor: User) -> None:
        self.contacts.delete(self.get_for_actor(contact_id, actor))
