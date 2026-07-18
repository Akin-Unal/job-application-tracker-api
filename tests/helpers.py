from typing import Any

from fastapi.testclient import TestClient

from app.core.config import get_settings

API_PREFIX = get_settings().api_v1_prefix


def create_company(
    client: TestClient,
    headers: dict[str, str],
    name: str = "Acme",
    **overrides: Any,
) -> dict[str, Any]:
    payload = {"name": name, **overrides}
    response = client.post(f"{API_PREFIX}/companies", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def create_application(
    client: TestClient,
    headers: dict[str, str],
    company_id: str,
    title: str = "Backend Engineer",
    **overrides: Any,
) -> dict[str, Any]:
    payload = {
        "company_id": company_id,
        "position_title": title,
        **overrides,
    }
    response = client.post(f"{API_PREFIX}/applications", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def transition(
    client: TestClient,
    headers: dict[str, str],
    application_id: str,
    new_status: str,
    note: str | None = None,
) -> dict[str, Any]:
    response = client.patch(
        f"{API_PREFIX}/applications/{application_id}/status",
        json={"status": new_status, "note": note},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()
