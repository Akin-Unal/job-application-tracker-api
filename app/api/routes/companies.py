from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.company import Company
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.schemas.contact import ContactCreate, ContactRead
from app.services.company_service import CompanyService
from app.services.contact_service import ContactService
from app.utils.pagination import PaginationParams, get_pagination_params

router = APIRouter(tags=["Companies"])


@router.post("/companies", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Company:
    return CompanyService(db).create(payload, current_user)


@router.get("/companies", response_model=PaginatedResponse[CompanyRead])
def list_companies(
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    industry: Annotated[str | None, Query()] = None,
    location: Annotated[str | None, Query()] = None,
    created_by_id: Annotated[UUID | None, Query(description="Admin only")] = None,
    q: Annotated[str | None, Query(min_length=1)] = None,
) -> PaginatedResponse[CompanyRead]:
    return CompanyService(db).list(
        params,
        current_user,
        industry=industry,
        location=location,
        created_by_id=created_by_id,
        q=q,
    )


@router.get("/companies/{company_id}", response_model=CompanyRead)
def get_company(
    company_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Company:
    return CompanyService(db).get_for_actor(company_id, current_user)


@router.patch("/companies/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Company:
    return CompanyService(db).update(company_id, payload, current_user)


@router.delete("/companies/{company_id}", response_model=MessageResponse)
def delete_company(
    company_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    CompanyService(db).delete(company_id, current_user)
    return MessageResponse(message="Company deleted")


@router.post(
    "/companies/{company_id}/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Contacts"],
)
def create_contact(
    company_id: UUID,
    payload: ContactCreate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> object:
    return ContactService(db).create(company_id, payload, current_user)


@router.get(
    "/companies/{company_id}/contacts",
    response_model=PaginatedResponse[ContactRead],
    tags=["Contacts"],
)
def list_company_contacts(
    company_id: UUID,
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PaginatedResponse[ContactRead]:
    return ContactService(db).list_for_company(company_id, params, current_user)
