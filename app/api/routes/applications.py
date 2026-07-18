from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.enums import (
    ApplicationPriority,
    ApplicationSource,
    ApplicationStatus,
    EmploymentType,
    WorkMode,
)
from app.models.job_application import JobApplication
from app.models.user import User
from app.schemas.application import (
    ApplicationArchiveRequest,
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatistics,
    ApplicationStatusUpdate,
    ApplicationUpdate,
)
from app.schemas.application_note import ApplicationNoteCreate, ApplicationNoteRead
from app.schemas.application_status_history import ApplicationStatusHistoryRead
from app.schemas.common import PaginatedResponse
from app.schemas.interview import InterviewCreate, InterviewRead
from app.services.application_note_service import ApplicationNoteService
from app.services.application_service import ApplicationService
from app.services.interview_service import InterviewService
from app.utils.pagination import PaginationParams, get_pagination_params

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobApplication:
    return ApplicationService(db).create(payload, current_user)


@router.get("", response_model=PaginatedResponse[ApplicationRead])
def list_applications(
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    application_status: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    priority: ApplicationPriority | None = None,
    source: ApplicationSource | None = None,
    work_mode: WorkMode | None = None,
    employment_type: EmploymentType | None = None,
    company_id: UUID | None = None,
    created_by_id: Annotated[UUID | None, Query(description="Admin only")] = None,
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
    deadline_from: datetime | None = None,
    deadline_to: datetime | None = None,
    is_archived: bool | None = None,
    q: Annotated[str | None, Query(min_length=1)] = None,
    sort_by: Literal[
        "created_at",
        "updated_at",
        "applied_at",
        "deadline_at",
        "last_activity_at",
        "priority",
        "status",
    ] = "created_at",
    sort_direction: Literal["asc", "desc"] = "desc",
) -> PaginatedResponse[ApplicationRead]:
    return ApplicationService(db).list(
        params,
        current_user,
        created_by_id=created_by_id,
        status=application_status,
        priority=priority,
        source=source,
        work_mode=work_mode,
        employment_type=employment_type,
        company_id=company_id,
        applied_from=applied_from,
        applied_to=applied_to,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        is_archived=is_archived,
        q=q,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


@router.get("/statistics", response_model=ApplicationStatistics, tags=["Statistics"])
def application_statistics(
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    created_by_id: Annotated[UUID | None, Query(description="Admin only")] = None,
) -> ApplicationStatistics:
    return ApplicationService(db).statistics(current_user, created_by_id)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobApplication:
    return ApplicationService(db).get_for_actor(application_id, current_user)


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobApplication:
    return ApplicationService(db).update(application_id, payload, current_user)


@router.patch("/{application_id}/status", response_model=ApplicationRead)
def change_application_status(
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> JobApplication:
    return ApplicationService(db).change_status(
        application_id, payload.status, current_user, payload.note
    )


@router.patch("/{application_id}/archive", response_model=ApplicationRead)
def archive_application(
    application_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    payload: ApplicationArchiveRequest | None = None,
) -> JobApplication:
    return ApplicationService(db).change_status(
        application_id,
        ApplicationStatus.ARCHIVED,
        current_user,
        payload.note if payload else None,
    )


@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationStatusHistoryRead],
    tags=["Application History"],
)
def application_history(
    application_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[ApplicationStatusHistoryRead]:
    return ApplicationService(db).history_for_actor(application_id, current_user)


@router.post(
    "/{application_id}/interviews",
    response_model=InterviewRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Interviews"],
)
def create_interview(
    application_id: UUID,
    payload: InterviewCreate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> object:
    return InterviewService(db).create(application_id, payload, current_user)


@router.get(
    "/{application_id}/interviews",
    response_model=PaginatedResponse[InterviewRead],
    tags=["Interviews"],
)
def list_application_interviews(
    application_id: UUID,
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> PaginatedResponse[InterviewRead]:
    return InterviewService(db).list(
        params,
        current_user,
        created_by_id=None,
        status=None,
        interview_type=None,
        scheduled_from=None,
        scheduled_to=None,
        application_id=application_id,
    )


@router.post(
    "/{application_id}/notes",
    response_model=ApplicationNoteRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Notes"],
)
def create_application_note(
    application_id: UUID,
    payload: ApplicationNoteCreate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> object:
    return ApplicationNoteService(db).create(application_id, payload, current_user)


@router.get(
    "/{application_id}/notes",
    response_model=list[ApplicationNoteRead],
    tags=["Notes"],
)
def list_application_notes(
    application_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> list[ApplicationNoteRead]:
    return ApplicationNoteService(db).list_for_application(application_id, current_user)
