from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.application_status_history import ApplicationStatusHistory
from app.models.company import Company
from app.models.enums import (
    ApplicationPriority,
    ApplicationSource,
    ApplicationStatus,
    EmploymentType,
    InterviewStatus,
    WorkMode,
)
from app.models.interview import Interview
from app.models.job_application import JobApplication
from app.repositories.base import BaseRepository

SORT_COLUMNS = {
    "created_at": JobApplication.created_at,
    "updated_at": JobApplication.updated_at,
    "applied_at": JobApplication.applied_at,
    "deadline_at": JobApplication.deadline_at,
    "last_activity_at": JobApplication.last_activity_at,
    "priority": JobApplication.priority,
    "status": JobApplication.status,
}


class ApplicationRepository(BaseRepository[JobApplication]):
    model = JobApplication

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_with_company(self, application_id: UUID) -> JobApplication | None:
        return self.db.scalar(
            select(JobApplication)
            .options(joinedload(JobApplication.company))
            .where(JobApplication.id == application_id)
        )

    def add_pending(self, application: JobApplication) -> None:
        self.db.add(application)
        self.db.flush()

    def commit_pending(self, application: JobApplication) -> JobApplication:
        self.db.commit()
        return self.get_with_company(application.id) or application

    def _filtered_statement(
        self,
        *,
        owner_id: UUID | None,
        status: ApplicationStatus | None = None,
        priority: ApplicationPriority | None = None,
        source: ApplicationSource | None = None,
        work_mode: WorkMode | None = None,
        employment_type: EmploymentType | None = None,
        company_id: UUID | None = None,
        applied_from: datetime | None = None,
        applied_to: datetime | None = None,
        deadline_from: datetime | None = None,
        deadline_to: datetime | None = None,
        is_archived: bool | None = None,
        q: str | None = None,
    ) -> Select[tuple[JobApplication]]:
        statement = select(JobApplication)
        if q:
            statement = statement.join(Company)
        if owner_id is not None:
            statement = statement.where(JobApplication.created_by_id == owner_id)
        if status is not None:
            statement = statement.where(JobApplication.status == status)
        if priority is not None:
            statement = statement.where(JobApplication.priority == priority)
        if source is not None:
            statement = statement.where(JobApplication.source == source)
        if work_mode is not None:
            statement = statement.where(JobApplication.work_mode == work_mode)
        if employment_type is not None:
            statement = statement.where(JobApplication.employment_type == employment_type)
        if company_id is not None:
            statement = statement.where(JobApplication.company_id == company_id)
        if applied_from is not None:
            statement = statement.where(JobApplication.applied_at >= applied_from)
        if applied_to is not None:
            statement = statement.where(JobApplication.applied_at <= applied_to)
        if deadline_from is not None:
            statement = statement.where(JobApplication.deadline_at >= deadline_from)
        if deadline_to is not None:
            statement = statement.where(JobApplication.deadline_at <= deadline_to)
        if is_archived is not None:
            statement = statement.where(
                JobApplication.archived_at.is_not(None)
                if is_archived
                else JobApplication.archived_at.is_(None)
            )
        if q:
            pattern = f"%{q}%"
            statement = statement.where(
                or_(
                    JobApplication.position_title.ilike(pattern),
                    JobApplication.job_url.ilike(pattern),
                    JobApplication.location.ilike(pattern),
                    Company.name.ilike(pattern),
                )
            )
        return statement

    def list(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str,
        sort_direction: str,
        **filters: Any,
    ) -> tuple[list[JobApplication], int]:
        filtered = self._filtered_statement(**filters)
        total_statement = select(func.count()).select_from(filtered.order_by(None).subquery())
        total = self.db.scalar(total_statement) or 0
        column = SORT_COLUMNS[sort_by]
        ordering = column.asc() if sort_direction == "asc" else column.desc()
        statement = (
            filtered.options(joinedload(JobApplication.company))
            .order_by(ordering, JobApplication.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).unique()), total

    def statistics(
        self, owner_id: UUID | None, now: datetime, week_start: datetime, month_start: datetime
    ) -> dict[str, int]:
        owner_filter = (JobApplication.created_by_id == owner_id,) if owner_id is not None else ()
        status_rows = self.db.execute(
            select(JobApplication.status, func.count())
            .where(*owner_filter)
            .group_by(JobApplication.status)
        ).all()
        counts = {status.value: count for status, count in status_rows}
        total = sum(counts.values())
        upcoming_filters = [
            Interview.scheduled_at >= now,
            Interview.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED]),
        ]
        upcoming_statement = select(func.count()).select_from(Interview)
        if owner_id is not None:
            upcoming_statement = upcoming_statement.join(JobApplication)
            upcoming_filters.append(JobApplication.created_by_id == owner_id)
        upcoming = self.db.scalar(upcoming_statement.where(*upcoming_filters)) or 0
        this_week = (
            self.db.scalar(
                select(func.count())
                .select_from(JobApplication)
                .where(*owner_filter, JobApplication.applied_at >= week_start)
            )
            or 0
        )
        this_month = (
            self.db.scalar(
                select(func.count())
                .select_from(JobApplication)
                .where(*owner_filter, JobApplication.applied_at >= month_start)
            )
            or 0
        )
        non_draft = total - counts.get(ApplicationStatus.DRAFT.value, 0)
        reached_filters = []
        offer_filters = []
        if owner_id is not None:
            reached_filters.append(JobApplication.created_by_id == owner_id)
            offer_filters.append(JobApplication.created_by_id == owner_id)
        reached = (
            self.db.scalar(
                select(func.count(distinct(ApplicationStatusHistory.application_id)))
                .join(JobApplication)
                .where(
                    *reached_filters,
                    ApplicationStatusHistory.new_status.in_(
                        [
                            ApplicationStatus.HR_SCREEN,
                            ApplicationStatus.TECHNICAL_INTERVIEW,
                            ApplicationStatus.FINAL_INTERVIEW,
                            ApplicationStatus.OFFER,
                        ]
                    ),
                )
            )
            or 0
        )
        offers = (
            self.db.scalar(
                select(func.count(distinct(ApplicationStatusHistory.application_id)))
                .join(JobApplication)
                .where(
                    *offer_filters,
                    ApplicationStatusHistory.new_status == ApplicationStatus.OFFER,
                )
            )
            or 0
        )
        result = {
            "total_applications": total,
            "upcoming_interviews": upcoming,
            "applications_this_week": this_week,
            "applications_this_month": this_month,
            "response_numerator": reached,
            "offer_numerator": offers,
            "non_draft": non_draft,
        }
        result.update(
            {status.value.lower(): counts.get(status.value, 0) for status in ApplicationStatus}
        )
        return result
