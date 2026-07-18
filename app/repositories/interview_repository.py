from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import InterviewStatus, InterviewType
from app.models.interview import Interview
from app.models.job_application import JobApplication
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    model = Interview

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_with_application(self, interview_id: UUID) -> Interview | None:
        return self.db.scalar(
            select(Interview)
            .options(joinedload(Interview.application))
            .where(Interview.id == interview_id)
        )

    def list(
        self,
        *,
        offset: int,
        limit: int,
        application_owner_id: UUID | None,
        created_by_id: UUID | None,
        status: InterviewStatus | None = None,
        interview_type: InterviewType | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        application_id: UUID | None = None,
    ) -> tuple[list[Interview], int]:
        filters = []
        statement = select(Interview)
        count_statement = select(func.count()).select_from(Interview)
        if application_owner_id is not None:
            statement = statement.join(JobApplication)
            count_statement = count_statement.join(JobApplication)
            filters.append(JobApplication.created_by_id == application_owner_id)
        if created_by_id is not None:
            filters.append(Interview.created_by_id == created_by_id)
        if status is not None:
            filters.append(Interview.status == status)
        if interview_type is not None:
            filters.append(Interview.interview_type == interview_type)
        if scheduled_from is not None:
            filters.append(Interview.scheduled_at >= scheduled_from)
        if scheduled_to is not None:
            filters.append(Interview.scheduled_at <= scheduled_to)
        if application_id is not None:
            filters.append(Interview.application_id == application_id)
        total = self.db.scalar(count_statement.where(*filters)) or 0
        statement = (
            statement.where(*filters)
            .order_by(Interview.scheduled_at.asc(), Interview.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement)), total

    def delete(self, interview: Interview) -> None:
        self.db.delete(interview)
        self.db.commit()
