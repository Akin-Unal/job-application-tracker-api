from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Job Application Tracker API", alias="APP_NAME")
    app_env: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        alias="APP_ENV",
    )
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/job_application_tracker_api_db",
        alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="change-this-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'.")
        return value.rstrip("/") or "/api/v1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        else:
            origins = value
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin.")
        for origin in origins:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError("CORS origins must be URLs or '*'.")
        return origins

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if len(value) < 12:
            raise ValueError("JWT_SECRET_KEY must be at least 12 characters long.")
        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_token_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive.")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
