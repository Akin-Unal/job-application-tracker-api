# Job Application Tracker API

A production-style job application tracking REST API built with FastAPI, PostgreSQL,
SQLAlchemy, Docker, JWT authentication and pytest.

Job Application Tracker API gives candidates one secure place to organize companies,
recruiting contacts, applications, interviews, notes, lifecycle history, and job-search
analytics. It is a backend portfolio project focused on practical REST design, relational
modeling, authorization, workflow rules, testing, and production-minded tooling.

> No public live demo is currently deployed. The project runs locally or with Docker Compose.

## Problem solved

Job searches quickly spread across bookmarks, inboxes, calendars, and spreadsheets. That makes
it difficult to answer basic questions: Which applications need attention? What interview is
next? How often do applications receive a response? This API models that information as a
permission-aware pipeline with immutable status history and useful aggregate metrics.

## Screenshots

The repository keeps `docs/images/` ready for real captures. Replace the placeholders after
starting the API; do not use fabricated screenshots.

### Swagger API Documentation

The API exposes interactive OpenAPI documentation through Swagger UI.  
Authentication is available through the JWT Bearer token flow.

![Swagger API Documentation](docs/images/swagger-overview.png)

---

### Application Endpoints

The application module includes endpoints for creating applications, listing applications, filtering, updating status, archiving, viewing history, and retrieving analytics.

![Application Endpoints](docs/images/application-endpoints.png)

---

### Automated Test Results

The project includes automated tests for authentication, companies, contacts, applications, workflow transitions, interviews, notes, statistics, and authorization rules.

![Automated Test Results](docs/images/test-results.png)

## Main features

- JWT registration, login, current-user access, and Swagger authorization
- Normal-user and administrator roles
- Owner-scoped companies, contacts, applications, interviews, and private notes
- Validated application lifecycle with automatic timestamps and status history
- Filtering, full-text-style search, sorting, and pagination
- Upcoming interview tracking and interview outcome states
- User-scoped and administrator-level application statistics
- SQLAlchemy 2.x repository and service layers
- PostgreSQL migrations with Alembic
- Isolated SQLite integration tests for fast local and CI execution
- Structured error responses that do not expose database details
- Docker Compose and GitHub Actions CI
- Ruff formatting/linting and strict mypy checks

## Architecture

The project uses a deliberately small layered architecture:

```text
HTTP request
  -> FastAPI route (input parsing and dependencies)
  -> service (authorization, ownership, workflow, timestamps)
  -> repository (queries, filtering, persistence, analytics)
  -> SQLAlchemy session
  -> PostgreSQL
```

Routes remain thin. Services are the security and business-rule boundary. Repositories own
database access, pagination, search, eager loading, history retrieval, and aggregate queries.
Application exceptions are converted to one stable JSON error envelope.

## Technology stack

| Area | Technology |
|---|---|
| API | Python 3.12, FastAPI, Uvicorn |
| Validation | Pydantic v2 |
| Persistence | PostgreSQL 16, SQLAlchemy 2.x, psycopg |
| Migrations | Alembic |
| Authentication | JWT bearer tokens, Argon2 password hashing |
| Testing | pytest, FastAPI TestClient, isolated SQLite database |
| Quality | Ruff, mypy |
| Delivery | Docker, Docker Compose, GitHub Actions |

## Database entities

- `users`: credentials, profile, role, and active state
- `companies`: owner-scoped employers with industry and location metadata
- `contacts`: recruiters, hiring managers, and referrals belonging to companies
- `job_applications`: position details, pipeline state, dates, compensation, and priority
- `application_status_history`: immutable creation and transition records
- `interviews`: scheduling, type, participant, location/link, and outcome
- `application_notes`: trimmed private notes attached to applications

```mermaid
erDiagram
    USER ||--o{ COMPANY : creates
    USER ||--o{ CONTACT : creates
    USER ||--o{ JOB_APPLICATION : creates
    USER ||--o{ INTERVIEW : creates
    USER ||--o{ APPLICATION_NOTE : authors
    USER ||--o{ APPLICATION_STATUS_HISTORY : changes
    COMPANY ||--o{ CONTACT : has
    COMPANY ||--o{ JOB_APPLICATION : receives
    JOB_APPLICATION ||--o{ APPLICATION_STATUS_HISTORY : records
    JOB_APPLICATION ||--o{ INTERVIEW : schedules
    JOB_APPLICATION ||--o{ APPLICATION_NOTE : contains

    USER {
        uuid id PK
        string email UK
        string full_name
        enum role
        boolean is_active
    }
    COMPANY {
        uuid id PK
        uuid created_by_id FK
        string name
        string industry
        string location
    }
    CONTACT {
        uuid id PK
        uuid company_id FK
        uuid created_by_id FK
        string full_name
        string email
    }
    JOB_APPLICATION {
        uuid id PK
        uuid company_id FK
        uuid created_by_id FK
        string position_title
        enum status
        enum priority
        datetime applied_at
        datetime archived_at
    }
    APPLICATION_STATUS_HISTORY {
        uuid id PK
        uuid application_id FK
        uuid changed_by_id FK
        enum old_status
        enum new_status
        datetime created_at
    }
    INTERVIEW {
        uuid id PK
        uuid application_id FK
        uuid created_by_id FK
        enum interview_type
        datetime scheduled_at
        enum status
    }
    APPLICATION_NOTE {
        uuid id PK
        uuid application_id FK
        uuid author_id FK
        text content
        boolean is_private
    }
```

Company names are unique per owner. Foreign-key indexes and common application filter indexes
are included in the domain migration.

## Application lifecycle

Every application starts as `DRAFT` unless an initial status is explicitly supplied. Creation
automatically produces a history row with a null old status. Every later status change is
validated by the service and creates exactly one additional history row.

- Entering `APPLIED` sets `applied_at` when it is not already set.
- Meaningful application, interview, or note activity updates `last_activity_at`.
- Entering `ARCHIVED` sets `archived_at`.
- Reopening an archived application clears `archived_at`.
- Route handlers never write status-history records directly.

## Status workflow

```mermaid
flowchart LR
    DRAFT --> APPLIED
    DRAFT --> WITHDRAWN
    APPLIED --> HR_SCREEN
    APPLIED --> REJECTED
    APPLIED --> WITHDRAWN
    HR_SCREEN --> TECHNICAL_INTERVIEW
    HR_SCREEN --> REJECTED
    HR_SCREEN --> WITHDRAWN
    TECHNICAL_INTERVIEW --> FINAL_INTERVIEW
    TECHNICAL_INTERVIEW --> REJECTED
    TECHNICAL_INTERVIEW --> WITHDRAWN
    FINAL_INTERVIEW --> OFFER
    FINAL_INTERVIEW --> REJECTED
    FINAL_INTERVIEW --> WITHDRAWN
    OFFER --> ARCHIVED
    OFFER --> WITHDRAWN
    REJECTED --> ARCHIVED
    WITHDRAWN --> ARCHIVED
    ARCHIVED --> APPLIED
```

An invalid transition returns HTTP `422` with code
`INVALID_APPLICATION_STATUS_TRANSITION`.

## Authorization rules

Normal users can manage only companies and applications they own, plus nested contacts,
interviews, history, and notes belonging to those records. Owner IDs are derived from the JWT;
clients cannot assign them. Passing another user's `created_by_id` does not bypass list
isolation.

Administrators can view and manage all domain records, view global statistics, and use
`created_by_id` filters. Registration always creates a normal user; administrator accounts are
created through the local CLI.

Company deletion is a permanent delete because the inherited template has no generic soft-delete
facility and the specified Company model has no archive timestamp. Database cascades remove its
dependent contacts and applications. Application archival is a workflow transition and is not
a physical delete.

## Folder structure

```text
.
├── alembic/
│   └── versions/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   └── routes/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── utils/
│   └── main.py
├── docs/images/
├── scripts/
├── tests/
│   ├── integration/
│   └── unit/
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Local installation

Requirements:

- Python 3.12
- PostgreSQL 16 or a compatible recent version
- Git
- Optional: Docker Desktop

```bash
git clone <repository-url>
cd job-application-tracker-api
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Replace `<repository-url>` with this repository's actual clone URL.

## PowerShell setup (Windows 11)

```powershell
git clone <repository-url>
Set-Location job-application-tracker-api
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If activation is restricted by organization policy, call the environment executable directly:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Environment variables

| Variable | Purpose | Local example |
|---|---|---|
| `APP_NAME` | Log/display name | `Job Application Tracker API` |
| `APP_ENV` | Environment name | `development` |
| `DEBUG` | FastAPI debug behavior | `true` |
| `API_V1_PREFIX` | Versioned API prefix | `/api/v1` |
| `DATABASE_URL` | SQLAlchemy connection URL | `postgresql+psycopg://postgres:postgres@localhost:5432/job_application_tracker_api_db` |
| `JWT_SECRET_KEY` | Token signing secret | Replace the example |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `CORS_ORIGINS` | Comma-separated browser origins | `http://localhost:3000,http://localhost:5173` |

`.env` is ignored by Git. Never commit a production database URL or signing key.

## PostgreSQL setup

Using `psql`:

```sql
CREATE DATABASE job_application_tracker_api_db;
CREATE USER job_tracker WITH PASSWORD 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON DATABASE job_application_tracker_api_db TO job_tracker;
```

Then set `DATABASE_URL` in `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://job_tracker:replace-with-a-strong-password@localhost:5432/job_application_tracker_api_db
```

For a simple local-only setup, the `.env.example` PostgreSQL superuser URL also matches the
Docker Compose service.

## Alembic migrations

Apply all migrations:

```powershell
python -m alembic upgrade head
```

Inspect migration state:

```powershell
python -m alembic current
python -m alembic heads
python -m alembic history
```

Create a future autogeneration:

```powershell
python -m alembic revision --autogenerate -m "describe change"
```

The domain migration adds all tracker tables, enum constraints, relationships, and indexes. It
also converts the original users primary key from its migration's `VARCHAR(36)` representation
to PostgreSQL UUID before creating UUID foreign keys.

## Running the API

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

Open:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

## Docker usage

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up -d --build
```

In another terminal:

```powershell
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m scripts.seed
```

Stop services while retaining PostgreSQL data:

```powershell
docker compose down
```

Remove the local database volume only when its data is no longer needed:

```powershell
docker compose down --volumes
```

## Running tests

Tests use an isolated SQLite database and reset schema state for every test.

```powershell
python -m pytest
python -m pytest tests\integration\test_applications.py
python -m pytest -k status_transition
```

Test order is not significant.

## Linting and type checking

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy app
```

To format locally:

```powershell
python -m ruff format .
```

## Creating an administrator

```powershell
python -m scripts.create_admin `
  --email admin@localhost.test `
  --password "Choose-A-Long-Random-Password" `
  --name "Local Administrator"
```

The script refuses to overwrite an existing account.

## Seeding demo data

Run migrations first, then:

```powershell
python -m scripts.seed
```

The seed is reasonably idempotent: it reuses users and recognizes its companies, contacts,
applications, interviews, and notes. Statuses are built through the real workflow service, so
demo history remains consistent.

Local development credentials:

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@example.com` | `DemoPassword123!` |
| Normal user | `alice@example.com` | `DemoPassword123!` |
| Normal user | `bob@example.com` | `DemoPassword123!` |

These credentials are intentionally public and are **only for local development**. Never use
them in staging or production.

## API endpoint summary

All business endpoints use `/api/v1`.

| Group | Method and path |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Users | `GET /users`, `GET/PATCH/DELETE /users/{user_id}` |
| Companies | `POST/GET /companies`, `GET/PATCH/DELETE /companies/{company_id}` |
| Contacts | `POST/GET /companies/{company_id}/contacts`, `GET/PATCH/DELETE /contacts/{contact_id}` |
| Applications | `POST/GET /applications`, `GET/PATCH /applications/{application_id}` |
| Workflow | `PATCH /applications/{application_id}/status`, `PATCH /applications/{application_id}/archive` |
| History | `GET /applications/{application_id}/history` |
| Interviews | `POST/GET /applications/{application_id}/interviews`, `GET /interviews`, `GET/PATCH/DELETE /interviews/{interview_id}` |
| Notes | `POST/GET /applications/{application_id}/notes`, `PATCH/DELETE /notes/{note_id}` |
| Statistics | `GET /applications/statistics` |
| Health | `GET /health`, `GET /api/v1/health`, `GET /api/v1/health/database` |

## Filtering examples

Applications support `status`, `priority`, `source`, `work_mode`, `employment_type`,
`company_id`, date ranges, `is_archived`, search, sorting, and pagination:

```http
GET /api/v1/applications?status=APPLIED&priority=HIGH&page=1&page_size=20
GET /api/v1/applications?q=backend&sort_by=deadline_at&sort_direction=asc
GET /api/v1/applications?applied_from=2026-07-01T00:00:00Z&applied_to=2026-07-31T23:59:59Z
GET /api/v1/applications?is_archived=false&work_mode=REMOTE
```

Company and interview examples:

```http
GET /api/v1/companies?q=fintech&industry=Software&page=1&page_size=10
GET /api/v1/interviews?status=SCHEDULED&interview_type=TECHNICAL
GET /api/v1/interviews?scheduled_from=2026-07-20T00:00:00Z&scheduled_to=2026-08-01T00:00:00Z
```

`created_by_id` is effective only for administrators. Invalid date ranges return
`INVALID_DATE_RANGE`.

## Authentication examples

Register:

```powershell
$registration = @{
  email = "candidate@example.com"
  password = "A-Strong-Password-123"
  full_name = "Example Candidate"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body $registration
```

Log in and call an authenticated endpoint:

```powershell
$login = @{
  email = "candidate@example.com"
  password = "A-Strong-Password-123"
} | ConvertTo-Json

$token = (Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/auth/login" `
  -ContentType "application/json" `
  -Body $login).access_token

$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications" -Headers $headers
```

In Swagger UI, choose **Authorize** and paste the JWT token. The HTTP bearer security scheme
adds it to subsequent requests.

## Status update example

```powershell
$body = @{
  status = "APPLIED"
  note = "Submitted through the company careers page."
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Patch `
  -Uri "http://localhost:8000/api/v1/applications/<application-id>/status" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Example business-rule error:

```json
{
  "error": {
    "code": "INVALID_APPLICATION_STATUS_TRANSITION",
    "message": "Application cannot transition from DRAFT to OFFER"
  }
}
```

## Statistics

`GET /api/v1/applications/statistics` returns status counts, upcoming interviews, weekly and
monthly application totals, response rate, and offer rate. Normal users see only their own
records. Administrators see global values unless they provide `created_by_id`.

Response rate counts distinct applications whose history reached `HR_SCREEN` or a later
interview/offer state, divided by current non-draft applications. Offer rate counts distinct
applications whose history reached `OFFER`, using the same denominator.

## GitHub Actions CI

`.github/workflows/ci.yml` runs on pushes and pull requests to `main`. It installs Python 3.12
dependencies and requires:

```text
ruff check .
ruff format --check .
mypy app
pytest
```

The CI test database is SQLite; PostgreSQL behavior is represented by the Alembic migration and
the Docker Compose development environment.

## Security notes

- Passwords are hashed with Argon2 and never returned by the API.
- JWT secrets must be random, long, environment-specific, and stored outside source control.
- Registration cannot create an administrator.
- Ownership is enforced in services, not trusted from request filters.
- Private notes are available only through the application owner boundary or to administrators.
- Database exceptions and stack traces are replaced by stable JSON errors.
- Configure narrow production CORS origins and disable debug mode.
- Add TLS at the reverse proxy or platform boundary.
- Rotate seeded credentials immediately if demo data is ever used outside an isolated machine.

## Future improvements

- Refresh-token rotation and token revocation
- Optional reminders and calendar integrations
- Resume and cover-letter attachment metadata
- Saved searches and configurable dashboard widgets
- PostgreSQL-backed integration-test job in CI
- Audit events for non-status edits
- CSV import/export
- Rate limiting and production observability