import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.main import app
from app.models.ai import AIRun
from app.schemas.auth import Role


@pytest.fixture
def owner_token() -> str:
    clinic_id = uuid.uuid4()
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "owner@carefamily.com",
            "role": Role.OWNER,
            "clinic_id": str(clinic_id),
        }
    )


@pytest.fixture
def platform_admin_token() -> str:
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "admin@platform.com",
            "role": Role.PLATFORM_ADMIN,
            "is_platform_admin": True,
        }
    )


@pytest.fixture
def doctor_token() -> str:
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "doc@carefamily.com",
            "role": Role.DOCTOR,
            "clinic_id": str(uuid.uuid4()),
        }
    )


@pytest.fixture
def sample_ai_run() -> AIRun:
    run = MagicMock(spec=AIRun)
    run.id = uuid.uuid4()
    run.clinic_id = uuid.uuid4()
    run.feature = "chat"
    run.requested_by = uuid.uuid4()
    run.provider = "openrouter"
    run.model = "google/gemini-flash"
    run.tools_called = ["get_my_token_status"]
    run.input_tokens = 120
    run.output_tokens = 45
    run.cost_usd = Decimal("0.000045")
    run.status = "success"
    run.error = None
    run.at = dt.datetime.now(dt.UTC)
    return run


@pytest.mark.asyncio
async def test_owner_can_view_ai_activity(owner_token: str, sample_ai_run: AIRun) -> None:
    """Acceptance test: Owner can retrieve AI telemetry log for their clinic (F-017)."""
    with patch("app.services.ai_service.AIService.get_activity_log") as mock_get_log:
        mock_get_log.return_value = ([sample_ai_run], 1)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get(
                "/api/v1/ai/activity",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

        item = data["items"][0]
        assert item["feature"] == "chat"
        assert item["provider"] == "openrouter"
        assert item["model"] == "google/gemini-flash"
        assert item["status"] == "success"
        assert item["input_tokens"] == 120
        assert item["output_tokens"] == 45
        assert Decimal(item["cost_usd"]) == Decimal("0.000045")
        assert "get_my_token_status" in item["tools_called"]


@pytest.mark.asyncio
async def test_platform_admin_can_view_ai_activity(
    platform_admin_token: str, sample_ai_run: AIRun
) -> None:
    """Acceptance test: Platform Admin can retrieve AI activity across clinics (F-017)."""
    with patch("app.services.ai_service.AIService.get_activity_log") as mock_get_log:
        mock_get_log.return_value = ([sample_ai_run], 1)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get(
                f"/api/v1/ai/activity?clinic_id={sample_ai_run.clinic_id}&feature=chat",
                headers={"Authorization": f"Bearer {platform_admin_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 1


@pytest.mark.asyncio
async def test_doctor_forbidden_from_ai_activity(doctor_token: str) -> None:
    """Acceptance test: Non-authorized roles receive 403 Forbidden."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/ai/activity",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_ai_activity_filters(owner_token: str, sample_ai_run: AIRun) -> None:
    """Acceptance test: Date range and feature filters are passed to service."""
    with patch("app.services.ai_service.AIService.get_activity_log") as mock_get_log:
        mock_get_log.return_value = ([sample_ai_run], 1)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get(
                "/api/v1/ai/activity?start_date=2026-11-01&end_date=2026-11-02&feature=chat",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        assert mock_get_log.call_count == 1
        _, kwargs = mock_get_log.call_args
        assert kwargs["start_date"] == dt.date(2026, 11, 1)
        assert kwargs["end_date"] == dt.date(2026, 11, 2)
        assert kwargs["feature"] == "chat"
