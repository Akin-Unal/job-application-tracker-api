from __future__ import annotations

import builtins
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ApplicationAccessDeniedError,
    ApplicationNotFoundError,
    InvalidApplicationStatusTransitionError,
    InvalidDateRangeError,
)
from app.models.application_status_history import ApplicationStatusHistory
from app.models.enums import ApplicationStatus
from app.models.job_application import JobApplication
from app.models.user import User, UserRole
from app.repositories.application_repository import ApplicationRepository
from app.repositories.application_status_history_repository import (
    ApplicationStatusHistoryRepository,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatistics,
    ApplicationUpdate,
)
from app.schemas.application_status_history import ApplicationStatusHistoryRead
from app.schemas.common import PaginatedResponse
from app.services.company_service import CompanyService
from app.utils.pagination import PaginationParams, total_pages

ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DRAFT: {ApplicationStatus.APPLIED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.APPLIED: {
        ApplicationStatus.HR_SCREEN,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.HR_SCREEN: {
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.TECHNICAL_INTERVIEW: {
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.FINAL_INTERVIEW: {
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.OFFER: {ApplicationStatus.ARCHIVED, ApplicationStatus.WITHDRAWN},
    ApplicationStatus.REJECTED: {ApplicationStatus.ARCHIVED},
    ApplicationStatus.WITHDRAWN: {ApplicationStatus.ARCHIVED},
    ApplicationStatus.ARCHIVED: {ApplicationStatus.APPLIED},
}


def utc_now() -> datetime:
    return datetime.now(UTC)


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.applications = ApplicationRepository(db)
        self.history = ApplicationStatusHistoryRepository(db)
        self.company_service = CompanyService(db)

    @staticmethod
    def _authorize(application: JobApplication, actor: User) -> None:
        if actor.role != UserRole.ADMIN and application.created_by_id != actor.id:
            raise ApplicationAccessDeniedError()

    def get_for_actor(self, application_id: UUID, actor: User) -> JobApplication:
        application = self.applications.get_with_company(application_id)
        if application is None:
            raise ApplicationNotFoundError()
        self._authorize(application, actor)
        return application

    def create(self, payload: ApplicationCreate, actor: User) -> JobApplication:
        self.company_service.get_for_actor(payload.company_id, actor)
        now = utc_now()
        values = payload.model_dump()
        if values.get("job_url") is not None:
            values["job_url"] = str(values["job_url"])
        if values.get("currency"):
            values["currency"] = str(values["currency"]).upper()
        application = JobApplication(
            created_by_id=actor.id,
            last_activity_at=now,
            archived_at=now if payload.status == ApplicationStatus.ARCHIVED else None,
            **values,
        )
        if payload.status == ApplicationStatus.APPLIED and application.applied_at is None:
            application.applied_at = now
        self.applications.add_pending(application)
        self.history.add(
            ApplicationStatusHistory(
                application_id=application.id,
                changed_by_id=actor.id,
                old_status=None,
                new_status=application.status,
            )
        )
        return self.applications.commit_pending(application)

    @staticmethod
    def _validate_date_ranges(
        applied_from: datetime | None,
        applied_to: datetime | None,
        deadline_from: datetime | None,
        deadline_to: datetime | None,
    ) -> None:
        if applied_from and applied_to and applied_from > applied_to:
            raise InvalidDateRangeError("applied_from must not be after applied_to")
        if deadline_from and deadline_to and deadline_from > deadline_to:
            raise InvalidDateRangeError("deadline_from must not be after deadline_to")

    def list(
        self,
        params: PaginationParams,
        actor: User,
        *,
        created_by_id: UUID | None,
        **filters: Any,
    ) -> PaginatedResponse[ApplicationRead]:
        self._validate_date_ranges(
            filters.get("applied_from"),
            filters.get("applied_to"),
            filters.get("deadline_from"),
            filters.get("deadline_to"),
        )
        owner_id = created_by_id if actor.role == UserRole.ADMIN else actor.id
        applications, total = self.applications.list(
            offset=params.offset,
            limit=params.page_size,
            owner_id=owner_id,
            **filters,
        )
        return PaginatedResponse[ApplicationRead](
            items=[ApplicationRead.model_validate(item) for item in applications],
            page=params.page,
            page_size=params.page_size,
            total=total,
            total_pages=total_pages(total, params.page_size),
        )

    def _change_status_pending(
        self,
        application: JobApplication,
        new_status: ApplicationStatus,
        actor: User,
        note: str | None,
    ) -> None:
        old_status = application.status
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            raise InvalidApplicationStatusTransitionError(
                f"Application cannot transition from {old_status.value} to {new_status.value}"
            )
        now = utc_now()
        application.status = new_status
        application.last_activity_at = now
        if new_status == ApplicationStatus.APPLIED and application.applied_at is None:
            application.applied_at = now
        if new_status == ApplicationStatus.ARCHIVED:
            application.archived_at = now
        elif old_status == ApplicationStatus.ARCHIVED:
            application.archived_at = None
        self.history.add(
            ApplicationStatusHistory(
                application_id=application.id,
                changed_by_id=actor.id,
                old_status=old_status,
                new_status=new_status,
                note=note.strip() if note and note.strip() else None,
            )
        )

    def change_status(
        self,
        application_id: UUID,
        new_status: ApplicationStatus,
        actor: User,
        note: str | None = None,
    ) -> JobApplication:
        application = self.get_for_actor(application_id, actor)
        self._change_status_pending(application, new_status, actor, note)
        return self.applications.commit_pending(application)

    def update(
        self, application_id: UUID, payload: ApplicationUpdate, actor: User
    ) -> JobApplication:
        application = self.get_for_actor(application_id, actor)
        values = payload.model_dump(exclude_unset=True)
        new_status = values.pop("status", None)
        if "company_id" in values and values["company_id"] is not None:
            self.company_service.get_for_actor(values["company_id"], actor)
        if values.get("job_url") is not None:
            values["job_url"] = str(values["job_url"])
        if values.get("currency"):
            values["currency"] = str(values["currency"]).upper()
        if new_status is not None:
            self._change_status_pending(application, new_status, actor, None)
        for field, value in values.items():
            setattr(application, field, value)
        if values:
            application.last_activity_at = utc_now()
        return self.applications.commit_pending(application)

    def history_for_actor(
        self, application_id: UUID, actor: User
    ) -> builtins.list[ApplicationStatusHistoryRead]:
        self.get_for_actor(application_id, actor)
        return [
            ApplicationStatusHistoryRead.model_validate(item)
            for item in self.history.list_for_application(application_id)
        ]

    def statistics(self, actor: User, created_by_id: UUID | None) -> ApplicationStatistics:
        owner_id = created_by_id if actor.role == UserRole.ADMIN else actor.id
        now = utc_now()
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start -= timedelta(days=week_start.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        metrics = self.applications.statistics(owner_id, now, week_start, month_start)
        denominator = metrics.pop("non_draft")
        response_numerator = metrics.pop("response_numerator")
        offer_numerator = metrics.pop("offer_numerator")
        response: dict[str, Any] = dict(metrics)
        response["response_rate_percent"] = (
            round(response_numerator / denominator * 100, 1) if denominator else 0.0
        )
        response["offer_rate_percent"] = (
            round(offer_numerator / denominator * 100, 1) if denominator else 0.0
        )
        return ApplicationStatistics.model_validate(response)
