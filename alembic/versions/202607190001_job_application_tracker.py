"""job application tracker domain

Revision ID: 202607190001
Revises: 202607080001
Create Date: 2026-07-19 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607190001"
down_revision: str | None = "202607080001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

uuid_type = postgresql.UUID(as_uuid=True)
work_mode = sa.Enum("REMOTE", "HYBRID", "ONSITE", "UNSPECIFIED", name="workmode", native_enum=False)
employment_type = sa.Enum(
    "FULL_TIME",
    "PART_TIME",
    "INTERNSHIP",
    "CONTRACT",
    "FREELANCE",
    "UNSPECIFIED",
    name="employmenttype",
    native_enum=False,
)
application_source = sa.Enum(
    "LINKEDIN",
    "COMPANY_WEBSITE",
    "REFERRAL",
    "RECRUITER",
    "JOB_BOARD",
    "EMAIL",
    "OTHER",
    name="applicationsource",
    native_enum=False,
)
application_status = sa.Enum(
    "DRAFT",
    "APPLIED",
    "HR_SCREEN",
    "TECHNICAL_INTERVIEW",
    "FINAL_INTERVIEW",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
    "ARCHIVED",
    name="applicationstatus",
    native_enum=False,
)
application_priority = sa.Enum(
    "LOW", "MEDIUM", "HIGH", name="applicationpriority", native_enum=False
)
interview_type = sa.Enum(
    "HR_SCREEN",
    "TECHNICAL",
    "SYSTEM_DESIGN",
    "BEHAVIORAL",
    "FINAL",
    "OTHER",
    name="interviewtype",
    native_enum=False,
)
interview_status = sa.Enum(
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    "RESCHEDULED",
    "NO_SHOW",
    name="interviewstatus",
    native_enum=False,
)


def timestamp_columns() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.alter_column(
        "users",
        "id",
        existing_type=sa.String(length=36),
        type_=uuid_type,
        existing_nullable=False,
        postgresql_using="id::uuid",
    )

    op.create_table(
        "companies",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid_type, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("created_by_id", "name", name="uq_companies_owner_name"),
    )
    op.create_index("ix_companies_created_by_id", "companies", ["created_by_id"])
    op.create_index("ix_companies_id", "companies", ["id"])
    op.create_index("ix_companies_name", "companies", ["name"])

    op.create_table(
        "contacts",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("company_id", uuid_type, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=160), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid_type, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_index("ix_contacts_id", "contacts", ["id"])

    op.create_table(
        "job_applications",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("company_id", uuid_type, nullable=False),
        sa.Column("position_title", sa.String(length=180), nullable=False),
        sa.Column("job_url", sa.String(length=2048), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("work_mode", work_mode, nullable=False),
        sa.Column("employment_type", employment_type, nullable=False),
        sa.Column("source", application_source, nullable=False),
        sa.Column("status", application_status, nullable=False),
        sa.Column("priority", application_priority, nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", uuid_type, nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "company_id",
        "created_by_id",
        "status",
        "priority",
        "source",
        "work_mode",
        "employment_type",
        "applied_at",
        "deadline_at",
        "created_at",
        "id",
    ):
        op.create_index(f"ix_job_applications_{column}", "job_applications", [column])

    op.create_table(
        "application_status_history",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("application_id", uuid_type, nullable=False),
        sa.Column("changed_by_id", uuid_type, nullable=False),
        sa.Column("old_status", application_status, nullable=True),
        sa.Column("new_status", application_status, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_application_status_history_application_id",
        "application_status_history",
        ["application_id"],
    )

    op.create_table(
        "interviews",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("application_id", uuid_type, nullable=False),
        sa.Column("interview_type", interview_type, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("location_or_link", sa.String(length=2048), nullable=True),
        sa.Column("interviewer_name", sa.String(length=255), nullable=True),
        sa.Column("interviewer_email", sa.String(length=255), nullable=True),
        sa.Column("status", interview_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid_type, nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interviews_application_id", "interviews", ["application_id"])
    op.create_index("ix_interviews_id", "interviews", ["id"])
    op.create_index("ix_interviews_scheduled_at", "interviews", ["scheduled_at"])
    op.create_index("ix_interviews_status", "interviews", ["status"])

    op.create_table(
        "application_notes",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("application_id", uuid_type, nullable=False),
        sa.Column("author_id", uuid_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        *timestamp_columns(),
        sa.ForeignKeyConstraint(["application_id"], ["job_applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_application_notes_application_id", "application_notes", ["application_id"])
    op.create_index("ix_application_notes_id", "application_notes", ["id"])


def downgrade() -> None:
    op.drop_index("ix_application_notes_id", table_name="application_notes")
    op.drop_index("ix_application_notes_application_id", table_name="application_notes")
    op.drop_table("application_notes")
    op.drop_index("ix_interviews_status", table_name="interviews")
    op.drop_index("ix_interviews_scheduled_at", table_name="interviews")
    op.drop_index("ix_interviews_id", table_name="interviews")
    op.drop_index("ix_interviews_application_id", table_name="interviews")
    op.drop_table("interviews")
    op.drop_index(
        "ix_application_status_history_application_id",
        table_name="application_status_history",
    )
    op.drop_table("application_status_history")
    for column in reversed(
        (
            "company_id",
            "created_by_id",
            "status",
            "priority",
            "source",
            "work_mode",
            "employment_type",
            "applied_at",
            "deadline_at",
            "created_at",
            "id",
        )
    ):
        op.drop_index(f"ix_job_applications_{column}", table_name="job_applications")
    op.drop_table("job_applications")
    op.drop_index("ix_contacts_id", table_name="contacts")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_index("ix_companies_id", table_name="companies")
    op.drop_index("ix_companies_created_by_id", table_name="companies")
    op.drop_table("companies")
    op.alter_column(
        "users",
        "id",
        existing_type=uuid_type,
        type_=sa.String(length=36),
        existing_nullable=False,
        postgresql_using="id::text",
    )
