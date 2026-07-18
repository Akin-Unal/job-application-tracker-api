from fastapi.testclient import TestClient


def test_health_endpoint_returns_success(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_database_health_endpoint_returns_success(client: TestClient) -> None:
    response = client.get("/api/v1/health/database")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
