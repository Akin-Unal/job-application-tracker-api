from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.user import User
from tests.conftest import auth_header

API_PREFIX = get_settings().api_v1_prefix


def test_normal_user_cannot_list_all_users(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")

    response = client.get(f"{API_PREFIX}/users", headers=headers)

    assert response.status_code == 403


def test_admin_can_list_users(client: TestClient, admin_user: User, normal_user: User) -> None:
    headers = auth_header(client, admin_user.email, "StrongPassword123")

    response = client.get(f"{API_PREFIX}/users", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_user_can_get_own_account(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")

    response = client.get(f"{API_PREFIX}/users/{normal_user.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == normal_user.email


def test_user_cannot_change_their_own_role(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")

    response = client.patch(
        f"{API_PREFIX}/users/{normal_user.id}",
        json={"role": "ADMIN"},
        headers=headers,
    )

    assert response.status_code == 403


def test_user_can_update_own_full_name(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")

    response = client.patch(
        f"{API_PREFIX}/users/{normal_user.id}",
        json={"full_name": "Updated Name"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"
    assert response.json()["role"] == "USER"


def test_admin_can_update_a_user(
    client: TestClient,
    admin_user: User,
    normal_user: User,
) -> None:
    headers = auth_header(client, admin_user.email, "StrongPassword123")

    response = client.patch(
        f"{API_PREFIX}/users/{normal_user.id}",
        json={"full_name": "Promoted User", "role": "ADMIN"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Promoted User"
    assert response.json()["role"] == "ADMIN"


def test_admin_can_deactivate_a_user(
    client: TestClient,
    admin_user: User,
    normal_user: User,
) -> None:
    headers = auth_header(client, admin_user.email, "StrongPassword123")

    response = client.delete(f"{API_PREFIX}/users/{normal_user.id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False
