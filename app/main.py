import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Application startup: %s", settings.app_name)
    yield
    logger.info("Application shutdown: %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
