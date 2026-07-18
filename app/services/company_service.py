from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CompanyAccessDeniedError,
    CompanyNotFoundError,
    ResourceAlreadyExistsError,
)
from app.models.company import Company
from app.models.user import User, UserRole
from app.repositories.company_repository import CompanyRepository
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.utils.pagination import PaginationParams, total_pages


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.companies = CompanyRepository(db)

    @staticmethod
    def _authorize(company: Company, actor: User) -> None:
        if actor.role != UserRole.ADMIN and company.created_by_id != actor.id:
            raise CompanyAccessDeniedError()

    def get_for_actor(self, company_id: UUID, actor: User) -> Company:
        company = self.companies.get(company_id)
        if company is None:
            raise CompanyNotFoundError()
        self._authorize(company, actor)
        return company

    def create(self, payload: CompanyCreate, actor: User) -> Company:
        name = payload.name.strip()
        if self.companies.get_by_owner_and_name(actor.id, name):
            raise ResourceAlreadyExistsError("You already have a company with this name")
        company = Company(
            name=name,
            website_url=str(payload.website_url) if payload.website_url else None,
            industry=payload.industry,
            location=payload.location,
            notes=payload.notes,
            created_by_id=actor.id,
        )
        try:
            return self.companies.add(company)
        except IntegrityError as exc:
            self.companies.db.rollback()
            raise ResourceAlreadyExistsError("You already have a company with this name") from exc

    def list(
        self,
        params: PaginationParams,
        actor: User,
        *,
        industry: str | None,
        location: str | None,
        created_by_id: UUID | None,
        q: str | None,
    ) -> PaginatedResponse[CompanyRead]:
        owner_id = created_by_id if actor.role == UserRole.ADMIN else actor.id
        companies, total = self.companies.list(
            offset=params.offset,
            limit=params.page_size,
            owner_id=owner_id,
            industry=industry,
            location=location,
            q=q,
        )
        return PaginatedResponse[CompanyRead](
            items=[CompanyRead.model_validate(item) for item in companies],
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages(total, params.page_size),
        )

    def update(self, company_id: UUID, payload: CompanyUpdate, actor: User) -> Company:
        company = self.get_for_actor(company_id, actor)
        values = payload.model_dump(exclude_unset=True)
        if "name" in values:
            name = str(values["name"]).strip()
            duplicate = self.companies.get_by_owner_and_name(company.created_by_id, name)
            if duplicate is not None and duplicate.id != company.id:
                raise ResourceAlreadyExistsError("A company with this name already exists")
            values["name"] = name
        if values.get("website_url") is not None:
            values["website_url"] = str(values["website_url"])
        for field, value in values.items():
            setattr(company, field, value)
        return self.companies.commit(company)

    def delete(self, company_id: UUID, actor: User) -> None:
        company = self.get_for_actor(company_id, actor)
        self.companies.delete(company)
