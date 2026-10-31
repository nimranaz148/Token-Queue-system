from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "clinic-api"
