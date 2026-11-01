from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    mock_session = AsyncMock()

    async def _override_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    app.dependency_overrides[get_db] = _override_db
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "clinic-api"
        assert data["db"] == "ok"
    finally:
        app.dependency_overrides.pop(get_db, None)
