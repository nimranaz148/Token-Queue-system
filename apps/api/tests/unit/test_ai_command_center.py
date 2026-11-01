import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

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
def receptionist_token() -> str:
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "reception@carefamily.com",
            "role": Role.RECEPTION,
            "clinic_id": str(uuid.uuid4()),
        }
    )


@pytest.fixture
def sample_kpis() -> dict:
    run = MagicMock(spec=AIRun)
    run.id = uuid.uuid4()
    run.clinic_id = uuid.uuid4()
    run.feature = "chat"
    run.requested_by = None
    run.provider = "openrouter"
    run.model = "google/gemini-flash"
    run.tools_called = ["get_my_token_status"]
    run.input_tokens = 100
    run.output_tokens = 40
    run.cost_usd = Decimal("0.000039")
    run.status = "success"
    run.error = None
    run.at = dt.datetime.now(dt.UTC)

    return {
        "ai_calls": 128,
        "failures": 2,
        "fallback_rate": 0.0156,
        "total_cost_usd": Decimal("0.045620"),
        "thumbs_down_rate": 0.05,
        "recent_runs": [run],
    }


@pytest.mark.asyncio
async def test_owner_can_access_ai_command_center(owner_token: str, sample_kpis: dict) -> None:
    """Acceptance test: Owner can open D-003 AI Command Center dashboard with computed KPIs."""
    with patch("app.services.ai_service.AIService.get_command_center_kpis") as mock_kpis:
        mock_kpis.return_value = sample_kpis

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get(
                "/api/v1/ai/command-center",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["ai_calls"] == 128
        assert data["failures"] == 2
        assert data["fallback_rate"] == 0.0156
        assert Decimal(data["total_cost_usd"]) == Decimal("0.045620")
        assert data["thumbs_down_rate"] == 0.05
        assert len(data["recent_runs"]) == 1


@pytest.mark.asyncio
async def test_platform_admin_can_filter_command_center(
    platform_admin_token: str, sample_kpis: dict
) -> None:
    """Acceptance test: Platform admin can access command center with optional clinic filter."""
    with patch("app.services.ai_service.AIService.get_command_center_kpis") as mock_kpis:
        mock_kpis.return_value = sample_kpis

        target_clinic = uuid.uuid4()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get(
                f"/api/v1/ai/command-center?clinic_id={target_clinic}",
                headers={"Authorization": f"Bearer {platform_admin_token}"},
            )

        assert res.status_code == 200
        _, kwargs = mock_kpis.call_args
        assert kwargs["filter_clinic_id"] == target_clinic


@pytest.mark.asyncio
async def test_receptionist_forbidden_from_command_center(receptionist_token: str) -> None:
    """Acceptance test: Receptionist role receives 403 Forbidden."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/ai/command-center",
            headers={"Authorization": f"Bearer {receptionist_token}"},
        )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_command_center_empty_dataset(owner_token: str) -> None:
    """Acceptance test: Empty dataset returns zeros, not an error."""
    empty_kpis = {
        "ai_calls": 0,
        "failures": 0,
        "fallback_rate": 0.0,
        "total_cost_usd": Decimal("0.000000"),
        "thumbs_down_rate": 0.0,
        "recent_runs": [],
    }
    with patch("app.services.ai_service.AIService.get_command_center_kpis") as mock_kpis:
        mock_kpis.return_value = empty_kpis

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get(
                "/api/v1/ai/command-center",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["ai_calls"] == 0
        assert data["failures"] == 0
        assert data["recent_runs"] == []
