from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_database_session
from app.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns basic service health.",
)
def root_health() -> dict[str, str]:
    return {"status": "healthy", "service": "job-application-tracker-api"}


@router.get(
    "/api/v1/health",
    summary="Versioned health check",
    description="Returns basic service health for API v1.",
)
def versioned_health() -> dict[str, str]:
    return {"status": "healthy", "service": get_settings().app_name}


@router.get(
    "/api/v1/health/database",
    summary="Database health check",
    description="Verifies that the configured database accepts a simple query.",
)
def database_health(db: Annotated[Session, Depends(get_database_session)]) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "service": get_settings().app_name}
