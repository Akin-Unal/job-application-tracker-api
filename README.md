# Job Application Tracker API

A reusable, production-style FastAPI backend foundation for portfolio and real-world API projects. It is designed to be copied, renamed, and extended into projects such as support ticket systems, uptime monitors, job application trackers, document managers, and inventory APIs.

This template includes authentication, user management, migrations, tests, Docker support, CI, linting, formatting, type checking, and helper scripts. It is intentionally practical rather than enterprise-heavy, so a junior-to-mid-level developer can understand and adapt it.

## Features

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- PostgreSQL for local and Docker development
- Isolated SQLite test database for pytest and CI
- JWT bearer authentication with password hashing
- Registration, login, current-user, admin-only, and active-user dependencies
- User CRUD-style management with soft deletion
- Reusable repository and service layers
- Consistent application error responses
- Pagination helpers and paginated user listing
- Structured standard-library logging
- Swagger at `/docs` and ReDoc at `/redoc`
- Dockerfile, Docker Compose, GitHub Actions, Ruff, mypy, pytest
- Cross-platform project copy script

This is a strong starter template, not a complete production security program. Before using it for real production traffic, add infrastructure hardening, secrets management, rate limiting, monitoring, backups, TLS, and a security review.

## Architecture

Routes handle HTTP input and output. Services own business rules. Repositories own database queries. Schemas validate request and response data. Models define database entities.

```text
job-application-tracker-api/
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   │   ├── auth.py
│   │   │   └── database.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   └── users.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── database/
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── models/
│   │   ├── base.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── base.py
│   │   └── user_repository.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── common.py
│   │   └── user.py
│   ├── services/
│   │   ├── auth_service.py
│   │   └── user_service.py
│   ├── utils/
│   │   └── pagination.py
│   └── main.py
├── alembic/
├── scripts/
├── tests/
├── .github/workflows/ci.yml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- Pydantic v2 and pydantic-settings
- PyJWT
- pwdlib with Argon2
- Pytest and HTTPX
- Docker and Docker Compose
- GitHub Actions
- Ruff and mypy

## Requirements

- Python 3.12+
- PostgreSQL 14+ for local database development
- Docker Desktop if using Docker Compose
- Git

Make is optional. Windows PowerShell commands are documented below.

## Local Installation

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment Configuration

Edit `.env` after copying `.env.example`.

```env
APP_NAME=Job Application Tracker API
APP_ENV=development
DEBUG=true
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/job_application_tracker_api_db

JWT_SECRET_KEY=change-this-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Use a long random `JWT_SECRET_KEY` outside local development. Do not commit `.env`.

## Database Setup

Create a PostgreSQL database named `job_application_tracker_api_db`, or adjust `DATABASE_URL` to match your local database.

PowerShell example with Docker only for PostgreSQL:

```powershell
docker run --name fastapi-template-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=job_application_tracker_api_db `
  -p 5432:5432 `
  -d postgres:16-alpine
```

## Running Migrations

```powershell
alembic upgrade head
```

Create a new migration:

```powershell
alembic revision --autogenerate -m "add tickets table"
```

Downgrade one migration:

```powershell
alembic downgrade -1
```

## Running the API

PowerShell:

```powershell
uvicorn app.main:app --reload
```

Open:

- API root health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Usage

Build and run the API with PostgreSQL:

```powershell
docker compose up --build
```

Stop services:

```powershell
docker compose down
```

Run migrations inside the API container:

```powershell
docker compose exec api alembic upgrade head
```

The API is available at `http://localhost:8000`, and Swagger is available at `http://localhost:8000/docs`.

## Running Tests

Tests use SQLite and do not touch the development PostgreSQL database.

```powershell
pytest
```

## Linting and Formatting

```powershell
ruff check .
ruff format .
mypy app
```

Optional Make targets:

```powershell
make test
make lint
make format
make typecheck
```

## API Endpoints

Health:

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/health/database`

Auth:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Users:

- `GET /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

## Authentication Example

Register:

```powershell
curl.exe -X POST "http://localhost:8000/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"user@example.com\",\"password\":\"StrongPassword123\",\"full_name\":\"Example User\"}"
```

Log in:

```powershell
curl.exe -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"user@example.com\",\"password\":\"StrongPassword123\"}"
```

Use the token:

```powershell
$token = "paste-access-token-here"
curl.exe "http://localhost:8000/api/v1/auth/me" `
  -H "Authorization: Bearer $token"
```

## Creating an Admin

After migrations have run:

```powershell
python scripts/create_admin.py --email admin@example.com --password StrongPassword123 --name "Admin User"
```

Seed development users:

```powershell
python scripts/seed.py
```

Seed data creates:

- `admin@example.com` with password `StrongPassword123`
- `user@example.com` with password `StrongPassword123`

Do not run seed scripts automatically in production.

## Creating a New Project From the Template

PowerShell:

```powershell
python scripts/create_project.py `
  --name "TicketFlow API" `
  --slug "ticketflow-api" `
  --destination "../ticketflow-api"
```

The script copies the template, excludes local caches and `.env`, replaces template names, generates the copied `.env.example`, and refuses to overwrite a non-empty destination unless `--force` is provided.

## GitHub Actions

CI runs on pushes to `main` and pull requests targeting `main`.

It performs:

1. Dependency installation
2. `ruff check .`
3. `ruff format --check .`
4. `mypy app`
5. `pytest`

The workflow uses SQLite for tests, so it does not require an external PostgreSQL service.

## Extending the Template

To add a new domain, such as tickets:

1. Add a SQLAlchemy model in `app/models/`.
2. Import it in `app/database/models.py`.
3. Add Pydantic schemas in `app/schemas/`.
4. Add a repository in `app/repositories/`.
5. Add business rules in `app/services/`.
6. Add routes in `app/api/routes/`.
7. Include the router in `app/api/router.py`.
8. Create and apply an Alembic migration.
9. Add unit and integration tests.

## Future Improvements

- Refresh tokens and token revocation
- Rate limiting
- Request ID middleware
- Production metrics and tracing
- Role and permission tables for larger products
- Background task integration in project-specific forks
- Deployment examples for common cloud platforms
- Password reset and email verification flows
