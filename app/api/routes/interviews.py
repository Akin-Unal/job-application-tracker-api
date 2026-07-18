from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_database_session
from app.models.enums import InterviewStatus, InterviewType
from app.models.interview import Interview
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.interview import InterviewRead, InterviewUpdate
from app.services.interview_service import InterviewService
from app.utils.pagination import PaginationParams, get_pagination_params

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.get("", response_model=PaginatedResponse[InterviewRead])
def list_interviews(
    params: Annotated[PaginationParams, Depends(get_pagination_params)],
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    interview_status: Annotated[InterviewStatus | None, Query(alias="status")] = None,
    interview_type: InterviewType | None = None,
    scheduled_from: datetime | None = None,
    scheduled_to: datetime | None = None,
    application_id: UUID | None = None,
    created_by_id: Annotated[UUID | None, Query(description="Admin only")] = None,
) -> PaginatedResponse[InterviewRead]:
    return InterviewService(db).list(
        params,
        current_user,
        created_by_id=created_by_id,
        status=interview_status,
        interview_type=interview_type,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        application_id=application_id,
    )


@router.get("/{interview_id}", response_model=InterviewRead)
def get_interview(
    interview_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Interview:
    return InterviewService(db).get_for_actor(interview_id, current_user)


@router.patch("/{interview_id}", response_model=InterviewRead)
def update_interview(
    interview_id: UUID,
    payload: InterviewUpdate,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Interview:
    return InterviewService(db).update(interview_id, payload, current_user)


@router.delete("/{interview_id}", response_model=MessageResponse)
def delete_interview(
    interview_id: UUID,
    db: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> MessageResponse:
    InterviewService(db).delete(interview_id, current_user)
    return MessageResponse(message="Interview deleted")
