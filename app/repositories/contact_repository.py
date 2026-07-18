from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.contact import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    model = Contact

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_with_company(self, contact_id: UUID) -> Contact | None:
        return self.db.scalar(
            select(Contact).options(joinedload(Contact.company)).where(Contact.id == contact_id)
        )

    def list_for_company(
        self, company_id: UUID, offset: int, limit: int
    ) -> tuple[list[Contact], int]:
        filters = (Contact.company_id == company_id,)
        total = self.db.scalar(select(func.count()).select_from(Contact).where(*filters)) or 0
        statement = (
            select(Contact)
            .where(*filters)
            .order_by(Contact.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement)), total

    def delete(self, contact: Contact) -> None:
        self.db.delete(contact)
        self.db.commit()
