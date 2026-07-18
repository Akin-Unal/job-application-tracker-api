from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import auth_header

API_PREFIX = get_settings().api_v1_prefix


def test_user_can_register(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "email": "new@example.com",
            "password": "StrongPassword123",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data


def test_duplicate_email_registration_fails(client: TestClient) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "StrongPassword123",
        "full_name": "Duplicate User",
    }
    first = client.post(f"{API_PREFIX}/auth/register", json=payload)
    second = client.post(f"{API_PREFIX}/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "RESOURCE_ALREADY_EXISTS"


def test_user_can_log_in(client: TestClient) -> None:
    client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPassword123",
            "full_name": "Login User",
        },
    )

    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "login@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_invalid_login_fails(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "missing@example.com", "password": "StrongPassword123"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_authenticated_user_can_access_me(client: TestClient) -> None:
    client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "email": "me@example.com",
            "password": "StrongPassword123",
            "full_name": "Me User",
        },
    )
    headers = auth_header(client, "me@example.com", "StrongPassword123")

    response = client.get(f"{API_PREFIX}/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_unauthenticated_user_cannot_access_protected_endpoint(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/auth/me")

    assert response.status_code == 401
