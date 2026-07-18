from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.user import User
from tests.conftest import auth_header
from tests.helpers import create_company

API_PREFIX = get_settings().api_v1_prefix


def test_authenticated_user_can_create_company(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    response = client.post(
        f"{API_PREFIX}/companies",
        json={"name": "Acme", "industry": "Software"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["created_by_id"] == str(normal_user.id)


def test_unauthenticated_user_cannot_create_company(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/companies", json={"name": "Acme"})
    assert response.status_code == 401


def test_user_lists_only_own_companies(
    client: TestClient, normal_user: User, second_user: User
) -> None:
    own_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    create_company(client, own_headers, "Own Company")
    create_company(client, other_headers, "Other Company")
    response = client.get(f"{API_PREFIX}/companies", headers=own_headers)
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "Own Company"


def test_user_cannot_view_another_users_company(
    client: TestClient, normal_user: User, second_user: User
) -> None:
    own_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    company = create_company(client, other_headers)
    response = client.get(f"{API_PREFIX}/companies/{company['id']}", headers=own_headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "COMPANY_ACCESS_DENIED"


def test_admin_can_view_all_companies(
    client: TestClient, admin_user: User, normal_user: User, second_user: User
) -> None:
    create_company(
        client,
        auth_header(client, normal_user.email, "StrongPassword123"),
        "First",
    )
    create_company(
        client,
        auth_header(client, second_user.email, "StrongPassword123"),
        "Second",
    )
    response = client.get(
        f"{API_PREFIX}/companies",
        headers=auth_header(client, admin_user.email, "StrongPassword123"),
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_company_search_and_pagination(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    create_company(client, headers, "Northwind Analytics")
    create_company(client, headers, "Contoso", notes="Northwind partner")
    create_company(client, headers, "Fabrikam")
    search = client.get(f"{API_PREFIX}/companies?q=Northwind", headers=headers)
    assert search.json()["total"] == 2
    page = client.get(f"{API_PREFIX}/companies?page=2&page_size=2", headers=headers)
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert len(page.json()["items"]) == 1


def test_contact_ownership_and_admin_access(
    client: TestClient, admin_user: User, normal_user: User, second_user: User
) -> None:
    owner_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    company = create_company(client, owner_headers)
    created = client.post(
        f"{API_PREFIX}/companies/{company['id']}/contacts",
        json={"full_name": "Recruiter", "email": "recruiter@example.com"},
        headers=owner_headers,
    )
    assert created.status_code == 201
    contact_id = created.json()["id"]
    denied_create = client.post(
        f"{API_PREFIX}/companies/{company['id']}/contacts",
        json={"full_name": "Intruder"},
        headers=other_headers,
    )
    assert denied_create.status_code == 403
    denied_get = client.get(f"{API_PREFIX}/contacts/{contact_id}", headers=other_headers)
    assert denied_get.status_code == 403
    admin_get = client.get(
        f"{API_PREFIX}/contacts/{contact_id}",
        headers=auth_header(client, admin_user.email, "StrongPassword123"),
    )
    assert admin_get.status_code == 200
