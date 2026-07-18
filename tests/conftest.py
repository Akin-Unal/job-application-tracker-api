import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-local-tests")

from app.api.dependencies.database import get_database_session
from app.core.config import get_settings
from app.core.security import hash_password
from app.database.base import Base
from app.main import app
from app.models.user import User, UserRole

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_database_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("StrongPassword123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def normal_user(db_session: Session) -> User:
    user = User(
        email="user@example.com",
        full_name="Normal User",
        hashed_password=hash_password("StrongPassword123"),
        role=UserRole.USER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        f"{get_settings().api_v1_prefix}/auth/login",
        json={"email": email, "password": password},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
