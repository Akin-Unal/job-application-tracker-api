from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.user import User
from tests.conftest import auth_header
from tests.helpers import create_application, create_company, transition

API_PREFIX = get_settings().api_v1_prefix


def test_create_application_defaults_and_initial_history(
    client: TestClient, normal_user: User
) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    company = create_company(client, headers)
    application = create_application(client, headers, company["id"])
    assert application["status"] == "DRAFT"
    assert application["priority"] == "MEDIUM"
    history = client.get(f"{API_PREFIX}/applications/{application['id']}/history", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["old_status"] is None
    assert history.json()[0]["new_status"] == "DRAFT"


def test_user_cannot_create_application_for_another_users_company(
    client: TestClient, normal_user: User, second_user: User
) -> None:
    owner_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    company = create_company(client, owner_headers)
    response = client.post(
        f"{API_PREFIX}/applications",
        json={"company_id": company["id"], "position_title": "Engineer"},
        headers=other_headers,
    )
    assert response.status_code == 403


def test_application_owner_scoping_admin_and_bypass_protection(
    client: TestClient, admin_user: User, normal_user: User, second_user: User
) -> None:
    first_headers = auth_header(client, normal_user.email, "StrongPassword123")
    second_headers = auth_header(client, second_user.email, "StrongPassword123")
    first_company = create_company(client, first_headers, "First")
    second_company = create_company(client, second_headers, "Second")
    create_application(client, first_headers, first_company["id"], "First Role")
    create_application(client, second_headers, second_company["id"], "Second Role")
    own = client.get(
        f"{API_PREFIX}/applications?created_by_id={second_user.id}",
        headers=first_headers,
    )
    assert own.json()["total"] == 1
    assert own.json()["items"][0]["position_title"] == "First Role"
    admin = client.get(
        f"{API_PREFIX}/applications",
        headers=auth_header(client, admin_user.email, "StrongPassword123"),
    )
    assert admin.json()["total"] == 2


def test_application_filters_search_and_pagination(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    company = create_company(client, headers, "Searchable Company")
    first = create_application(
        client, headers, company["id"], "Python Backend Engineer", priority="HIGH"
    )
    create_application(client, headers, company["id"], "Designer", priority="LOW")
    transition(client, headers, first["id"], "APPLIED")
    status_result = client.get(f"{API_PREFIX}/applications?status=APPLIED", headers=headers)
    assert status_result.json()["total"] == 1
    priority_result = client.get(f"{API_PREFIX}/applications?priority=HIGH", headers=headers)
    assert priority_result.json()["total"] == 1
    search_result = client.get(f"{API_PREFIX}/applications?q=Python", headers=headers)
    assert search_result.json()["items"][0]["position_title"] == "Python Backend Engineer"
    page = client.get(f"{API_PREFIX}/applications?page=2&page_size=1", headers=headers)
    assert page.json()["total"] == 2
    assert len(page.json()["items"]) == 1


def test_valid_and_invalid_status_transitions(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    company = create_company(client, headers)
    application = create_application(client, headers, company["id"])
    applied = transition(client, headers, application["id"], "APPLIED", "Submitted")
    assert applied["applied_at"] is not None
    invalid = client.patch(
        f"{API_PREFIX}/applications/{application['id']}/status",
        json={"status": "OFFER"},
        headers=headers,
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_APPLICATION_STATUS_TRANSITION"


def test_archiving_reopening_and_complete_history(client: TestClient, normal_user: User) -> None:
    headers = auth_header(client, normal_user.email, "StrongPassword123")
    company = create_company(client, headers)
    application = create_application(client, headers, company["id"])
    for new_status in (
        "APPLIED",
        "HR_SCREEN",
        "TECHNICAL_INTERVIEW",
        "FINAL_INTERVIEW",
        "OFFER",
        "ARCHIVED",
    ):
        application = transition(client, headers, application["id"], new_status)
    assert application["archived_at"] is not None
    reopened = transition(client, headers, application["id"], "APPLIED")
    assert reopened["archived_at"] is None
    history = client.get(f"{API_PREFIX}/applications/{application['id']}/history", headers=headers)
    assert len(history.json()) == 8
