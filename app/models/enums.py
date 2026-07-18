import enum


class WorkMode(str, enum.Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    UNSPECIFIED = "UNSPECIFIED"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    INTERNSHIP = "INTERNSHIP"
    CONTRACT = "CONTRACT"
    FREELANCE = "FREELANCE"
    UNSPECIFIED = "UNSPECIFIED"


class ApplicationSource(str, enum.Enum):
    LINKEDIN = "LINKEDIN"
    COMPANY_WEBSITE = "COMPANY_WEBSITE"
    REFERRAL = "REFERRAL"
    RECRUITER = "RECRUITER"
    JOB_BOARD = "JOB_BOARD"
    EMAIL = "EMAIL"
    OTHER = "OTHER"


class ApplicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPLIED = "APPLIED"
    HR_SCREEN = "HR_SCREEN"
    TECHNICAL_INTERVIEW = "TECHNICAL_INTERVIEW"
    FINAL_INTERVIEW = "FINAL_INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ARCHIVED = "ARCHIVED"


class ApplicationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InterviewType(str, enum.Enum):
    HR_SCREEN = "HR_SCREEN"
    TECHNICAL = "TECHNICAL"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    BEHAVIORAL = "BEHAVIORAL"
    FINAL = "FINAL"
    OTHER = "OTHER"


class InterviewStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    NO_SHOW = "NO_SHOW"
