from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.application_note import ApplicationNote
from app.models.company import Company
from app.models.contact import Contact
from app.models.enums import (
    ApplicationPriority,
    ApplicationSource,
    ApplicationStatus,
    EmploymentType,
    InterviewStatus,
    InterviewType,
    WorkMode,
)
from app.models.interview import Interview
from app.models.job_application import JobApplication
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.application import ApplicationCreate
from app.schemas.application_note import ApplicationNoteCreate
from app.schemas.company import CompanyCreate
from app.schemas.contact import ContactCreate
from app.schemas.interview import InterviewCreate
from app.services.application_note_service import ApplicationNoteService
from app.services.application_service import ApplicationService
from app.services.company_service import CompanyService
from app.services.contact_service import ContactService
from app.services.interview_service import InterviewService

DEMO_PASSWORD = "DemoPassword123!"

STATUS_PATHS: dict[ApplicationStatus, tuple[ApplicationStatus, ...]] = {
    ApplicationStatus.DRAFT: (),
    ApplicationStatus.APPLIED: (ApplicationStatus.APPLIED,),
    ApplicationStatus.HR_SCREEN: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.HR_SCREEN,
    ),
    ApplicationStatus.TECHNICAL_INTERVIEW: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.HR_SCREEN,
        ApplicationStatus.TECHNICAL_INTERVIEW,
    ),
    ApplicationStatus.FINAL_INTERVIEW: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.HR_SCREEN,
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.FINAL_INTERVIEW,
    ),
    ApplicationStatus.OFFER: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.HR_SCREEN,
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.OFFER,
    ),
    ApplicationStatus.REJECTED: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.REJECTED,
    ),
    ApplicationStatus.WITHDRAWN: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.WITHDRAWN,
    ),
    ApplicationStatus.ARCHIVED: (
        ApplicationStatus.APPLIED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ARCHIVED,
    ),
}


def ensure_user(db: Session, email: str, full_name: str, role: UserRole) -> tuple[User, bool]:
    repository = UserRepository(db)
    user = repository.get_by_email(email)
    if user is not None:
        return user, False
    return (
        repository.add(
            User(
                email=email,
                full_name=full_name,
                hashed_password=hash_password(DEMO_PASSWORD),
                role=role,
            )
        ),
        True,
    )


def ensure_company(db: Session, actor: User, name: str, industry: str, location: str) -> Company:
    existing = db.scalar(
        select(Company).where(
            Company.created_by_id == actor.id,
            Company.name == name,
        )
    )
    if existing is not None:
        return existing
    return CompanyService(db).create(
        CompanyCreate(
            name=name,
            website_url=f"https://{name.lower().replace(' ', '')}.example.com",
            industry=industry,
            location=location,
            notes="Demo company created by scripts/seed.py.",
        ),
        actor,
    )


def ensure_contact(db: Session, actor: User, company: Company, name: str, role: str) -> Contact:
    existing = db.scalar(
        select(Contact).where(
            Contact.company_id == company.id,
            Contact.full_name == name,
        )
    )
    if existing is not None:
        return existing
    return ContactService(db).create(
        company.id,
        ContactCreate(
            full_name=name,
            email=f"{name.lower().replace(' ', '.')}@example.com",
            role=role,
            linkedin_url="https://www.linkedin.com/",
            notes="Demo contact.",
        ),
        actor,
    )


def ensure_application(
    db: Session,
    actor: User,
    company: Company,
    title: str,
    target_status: ApplicationStatus,
    priority: ApplicationPriority,
) -> JobApplication:
    existing = db.scalar(
        select(JobApplication).where(
            JobApplication.created_by_id == actor.id,
            JobApplication.company_id == company.id,
            JobApplication.position_title == title,
        )
    )
    if existing is not None:
        return existing
    service = ApplicationService(db)
    application = service.create(
        ApplicationCreate(
            company_id=company.id,
            position_title=title,
            location=company.location,
            work_mode=WorkMode.HYBRID,
            employment_type=EmploymentType.FULL_TIME,
            source=ApplicationSource.LINKEDIN,
            priority=priority,
            salary_min=70000,
            salary_max=100000,
            currency="USD",
            deadline_at=datetime.now(UTC) + timedelta(days=14),
        ),
        actor,
    )
    for status in STATUS_PATHS[target_status]:
        application = service.change_status(
            application.id,
            status,
            actor,
            "Demo lifecycle transition.",
        )
    return application


def ensure_interview(
    db: Session,
    actor: User,
    application: JobApplication,
    interview_type: InterviewType,
    status: InterviewStatus,
    days_from_now: int,
    marker: str,
) -> Interview:
    existing = db.scalar(
        select(Interview).where(
            Interview.application_id == application.id,
            Interview.interviewer_name == marker,
        )
    )
    if existing is not None:
        return existing
    return InterviewService(db).create(
        application.id,
        InterviewCreate(
            interview_type=interview_type,
            scheduled_at=datetime.now(UTC) + timedelta(days=days_from_now),
            duration_minutes=60,
            location_or_link="https://meet.example.com/demo-interview",
            interviewer_name=marker,
            interviewer_email="interviewer@example.com",
            status=status,
            notes="Demo interview.",
        ),
        actor,
    )


def ensure_note(
    db: Session, actor: User, application: JobApplication, content: str
) -> ApplicationNote:
    existing = db.scalar(
        select(ApplicationNote).where(
            ApplicationNote.application_id == application.id,
            ApplicationNote.content == content,
        )
    )
    if existing is not None:
        return existing
    return ApplicationNoteService(db).create(
        application.id,
        ApplicationNoteCreate(content=content, is_private=True),
        actor,
    )


def seed(db: Session) -> int:
    admin, admin_created = ensure_user(
        db, "admin@example.com", "Demo Administrator", UserRole.ADMIN
    )
    alice, alice_created = ensure_user(db, "alice@example.com", "Alice Candidate", UserRole.USER)
    bob, bob_created = ensure_user(db, "bob@example.com", "Bob Candidate", UserRole.USER)

    acme = ensure_company(db, alice, "Acme Labs", "Software", "Istanbul, Türkiye")
    northstar = ensure_company(db, alice, "Northstar AI", "Artificial Intelligence", "Remote")
    contoso = ensure_company(db, bob, "Contoso", "Financial Technology", "Ankara, Türkiye")
    ensure_contact(db, alice, acme, "Rana Recruiter", "Technical Recruiter")
    ensure_contact(db, alice, northstar, "Mert Manager", "Engineering Manager")
    ensure_contact(db, bob, contoso, "Selin Talent", "Talent Partner")

    alice_offer = ensure_application(
        db,
        alice,
        acme,
        "Senior Backend Engineer",
        ApplicationStatus.OFFER,
        ApplicationPriority.HIGH,
    )
    alice_interview = ensure_application(
        db,
        alice,
        northstar,
        "Platform Engineer",
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationPriority.HIGH,
    )
    ensure_application(
        db,
        alice,
        northstar,
        "API Engineer",
        ApplicationStatus.DRAFT,
        ApplicationPriority.MEDIUM,
    )
    bob_rejected = ensure_application(
        db,
        bob,
        contoso,
        "Python Developer",
        ApplicationStatus.REJECTED,
        ApplicationPriority.MEDIUM,
    )
    bob_applied = ensure_application(
        db,
        bob,
        contoso,
        "Integration Engineer",
        ApplicationStatus.APPLIED,
        ApplicationPriority.LOW,
    )

    ensure_interview(
        db,
        alice,
        alice_interview,
        InterviewType.TECHNICAL,
        InterviewStatus.SCHEDULED,
        3,
        "Upcoming Demo Interview",
    )
    ensure_interview(
        db,
        alice,
        alice_offer,
        InterviewType.FINAL,
        InterviewStatus.COMPLETED,
        -7,
        "Completed Demo Interview",
    )
    ensure_note(db, alice, alice_offer, "Review offer details and benefits.")
    ensure_note(db, alice, alice_interview, "Prepare system design examples.")
    ensure_note(db, bob, bob_rejected, "Ask for feedback after the rejection.")
    ensure_note(db, bob, bob_applied, "Follow up if there is no response in one week.")

    created_count = sum((admin_created, alice_created, bob_created))
    print(f"Demo seed complete. {created_count} user account(s) created.")
    print("Existing domain records are reused, making repeated runs safe.")
    print(f"Admin: {admin.email}")
    return 0


def main() -> int:
    db = SessionLocal()
    try:
        return seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
