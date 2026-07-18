from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models.user import User
from tests.conftest import auth_header
from tests.helpers import create_application, create_company, transition

API_PREFIX = get_settings().api_v1_prefix


def test_interview_ownership_listing_filters_and_admin_access(
    client: TestClient, admin_user: User, normal_user: User, second_user: User
) -> None:
    owner_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    company = create_company(client, owner_headers)
    application = create_application(client, owner_headers, company["id"])
    scheduled_at = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    created = client.post(
        f"{API_PREFIX}/applications/{application['id']}/interviews",
        json={"interview_type": "TECHNICAL", "scheduled_at": scheduled_at},
        headers=owner_headers,
    )
    assert created.status_code == 201
    interview_id = created.json()["id"]
    denied = client.post(
        f"{API_PREFIX}/applications/{application['id']}/interviews",
        json={"interview_type": "HR_SCREEN", "scheduled_at": scheduled_at},
        headers=other_headers,
    )
    assert denied.status_code == 403
    upcoming = client.get(
        f"{API_PREFIX}/interviews",
        params={"scheduled_from": datetime.now(UTC).isoformat()},
        headers=owner_headers,
    )
    assert upcoming.json()["total"] == 1
    filtered = client.get(
        f"{API_PREFIX}/interviews?interview_type=TECHNICAL&status=SCHEDULED",
        headers=owner_headers,
    )
    assert filtered.json()["total"] == 1
    denied_get = client.get(f"{API_PREFIX}/interviews/{interview_id}", headers=other_headers)
    assert denied_get.status_code == 403
    admin_get = client.get(
        f"{API_PREFIX}/interviews/{interview_id}",
        headers=auth_header(client, admin_user.email, "StrongPassword123"),
    )
    assert admin_get.status_code == 200
    admin_headers = auth_header(client, admin_user.email, "StrongPassword123")
    admin_created = client.post(
        f"{API_PREFIX}/applications/{application['id']}/interviews",
        json={"interview_type": "BEHAVIORAL", "scheduled_at": scheduled_at},
        headers=admin_headers,
    )
    assert admin_created.status_code == 201
    owner_list = client.get(f"{API_PREFIX}/interviews", headers=owner_headers)
    assert owner_list.json()["total"] == 2


def test_notes_are_trimmed_reject_empty_and_enforce_ownership(
    client: TestClient, normal_user: User, second_user: User
) -> None:
    owner_headers = auth_header(client, normal_user.email, "StrongPassword123")
    other_headers = auth_header(client, second_user.email, "StrongPassword123")
    company = create_company(client, owner_headers)
    application = create_application(client, owner_headers, company["id"])
    created = client.post(
        f"{API_PREFIX}/applications/{application['id']}/notes",
        json={"content": "  Follow up Friday  "},
        headers=owner_headers,
    )
    assert created.status_code == 201
    assert created.json()["content"] == "Follow up Friday"
    empty = client.post(
        f"{API_PREFIX}/applications/{application['id']}/notes",
        json={"content": "   "},
        headers=owner_headers,
    )
    assert empty.status_code == 422
    denied_add = client.post(
        f"{API_PREFIX}/applications/{application['id']}/notes",
        json={"content": "Not mine"},
        headers=other_headers,
    )
    assert denied_add.status_code == 403
    denied_list = client.get(
        f"{API_PREFIX}/applications/{application['id']}/notes",
        headers=other_headers,
    )
    assert denied_list.status_code == 403


def test_statistics_are_permission_aware_and_rates_are_correct(
    client: TestClient, admin_user: User, normal_user: User, second_user: User
) -> None:
    first_headers = auth_header(client, normal_user.email, "StrongPassword123")
    second_headers = auth_header(client, second_user.email, "StrongPassword123")
    first_company = create_company(client, first_headers, "First")
    second_company = create_company(client, second_headers, "Second")
    offer_application = create_application(client, first_headers, first_company["id"], "Offer Role")
    for new_status in (
        "APPLIED",
        "HR_SCREEN",
        "TECHNICAL_INTERVIEW",
        "FINAL_INTERVIEW",
        "OFFER",
    ):
        offer_application = transition(client, first_headers, offer_application["id"], new_status)
    create_application(client, first_headers, first_company["id"], "Draft Role")
    other_application = create_application(
        client, second_headers, second_company["id"], "Other Applied Role"
    )
    transition(client, second_headers, other_application["id"], "APPLIED")
    client.post(
        f"{API_PREFIX}/applications/{offer_application['id']}/interviews",
        json={
            "interview_type": "FINAL",
            "scheduled_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
        headers=first_headers,
    )
    user_stats = client.get(f"{API_PREFIX}/applications/statistics", headers=first_headers).json()
    assert user_stats["total_applications"] == 2
    assert user_stats["response_rate_percent"] == 100.0
    assert user_stats["offer_rate_percent"] == 100.0
    assert user_stats["upcoming_interviews"] == 1
    admin_stats = client.get(
        f"{API_PREFIX}/applications/statistics",
        headers=auth_header(client, admin_user.email, "StrongPassword123"),
    ).json()
    assert admin_stats["total_applications"] == 3
    assert admin_stats["response_rate_percent"] == 50.0
    assert admin_stats["offer_rate_percent"] == 50.0
