from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import InterviewNotFoundError, InvalidDateRangeError
from app.models.enums import InterviewStatus, InterviewType
from app.models.interview import Interview
from app.models.user import User, UserRole
from app.repositories.interview_repository import InterviewRepository
from app.schemas.common import PaginatedResponse
from app.schemas.interview import InterviewCreate, InterviewRead, InterviewUpdate
from app.services.application_service import ApplicationService, utc_now
from app.utils.pagination import PaginationParams, total_pages


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.interviews = InterviewRepository(db)
        self.application_service = ApplicationService(db)

    def get_for_actor(self, interview_id: UUID, actor: User) -> Interview:
        interview = self.interviews.get_with_application(interview_id)
        if interview is None:
            raise InterviewNotFoundError()
        self.application_service._authorize(interview.application, actor)
        return interview

    def create(self, application_id: UUID, payload: InterviewCreate, actor: User) -> Interview:
        application = self.application_service.get_for_actor(application_id, actor)
        values = payload.model_dump()
        if values.get("interviewer_email") is not None:
            values["interviewer_email"] = str(values["interviewer_email"])
        interview = Interview(
            application_id=application_id,
            created_by_id=actor.id,
            **values,
        )
        application.last_activity_at = utc_now()
        return self.interviews.add(interview)

    def list(
        self,
        params: PaginationParams,
        actor: User,
        *,
        created_by_id: UUID | None,
        status: InterviewStatus | None,
        interview_type: InterviewType | None,
        scheduled_from: datetime | None,
        scheduled_to: datetime | None,
        application_id: UUID | None,
    ) -> PaginatedResponse[InterviewRead]:
        if scheduled_from and scheduled_to and scheduled_from > scheduled_to:
            raise InvalidDateRangeError("scheduled_from must not be after scheduled_to")
        if application_id is not None:
            self.application_service.get_for_actor(application_id, actor)
        application_owner_id = actor.id if actor.role != UserRole.ADMIN else None
        creator_id = created_by_id if actor.role == UserRole.ADMIN else None
        interviews, total = self.interviews.list(
            offset=params.offset,
            limit=params.page_size,
            application_owner_id=application_owner_id,
            created_by_id=creator_id,
            status=status,
            interview_type=interview_type,
            scheduled_from=scheduled_from,
            scheduled_to=scheduled_to,
            application_id=application_id,
        )
        return PaginatedResponse[InterviewRead](
            items=[InterviewRead.model_validate(item) for item in interviews],
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages(total, params.page_size),
        )

    def update(self, interview_id: UUID, payload: InterviewUpdate, actor: User) -> Interview:
        interview = self.get_for_actor(interview_id, actor)
        values = payload.model_dump(exclude_unset=True)
        if values.get("interviewer_email") is not None:
            values["interviewer_email"] = str(values["interviewer_email"])
        for field, value in values.items():
            setattr(interview, field, value)
        interview.application.last_activity_at = utc_now()
        return self.interviews.commit(interview)

    def delete(self, interview_id: UUID, actor: User) -> None:
        interview = self.get_for_actor(interview_id, actor)
        interview.application.last_activity_at = utc_now()
        self.interviews.delete(interview)
