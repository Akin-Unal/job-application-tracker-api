from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_owner_and_name(self, owner_id: UUID, name: str) -> Company | None:
        return self.db.scalar(
            select(Company).where(
                Company.created_by_id == owner_id,
                func.lower(Company.name) == name.lower(),
            )
        )

    def list(
        self,
        *,
        offset: int,
        limit: int,
        owner_id: UUID | None,
        industry: str | None,
        location: str | None,
        q: str | None,
    ) -> tuple[list[Company], int]:
        filters = []
        if owner_id is not None:
            filters.append(Company.created_by_id == owner_id)
        if industry:
            filters.append(func.lower(Company.industry) == industry.lower())
        if location:
            filters.append(func.lower(Company.location).contains(location.lower()))
        if q:
            pattern = f"%{q}%"
            filters.append(
                or_(
                    Company.name.ilike(pattern),
                    Company.website_url.ilike(pattern),
                    Company.notes.ilike(pattern),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(Company).where(*filters)) or 0
        statement = (
            select(Company)
            .where(*filters)
            .order_by(Company.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement)), total

    def delete(self, company: Company) -> None:
        self.db.delete(company)
        self.db.commit()
