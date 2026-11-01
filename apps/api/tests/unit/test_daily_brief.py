import datetime as dt
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token
from app.main import app
from app.models.ai import AIBrief
from app.schemas.auth import Role


@pytest.fixture
def clinic_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def owner_token(clinic_id: uuid.UUID) -> str:
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "owner@carefamily.com",
            "role": Role.OWNER,
            "clinic_id": str(clinic_id),
        }
    )


@pytest.fixture
def doctor_token(clinic_id: uuid.UUID) -> str:
    return create_access_token(
        data={
            "sub": str(uuid.uuid4()),
            "email": "doc@carefamily.com",
            "role": Role.DOCTOR,
            "clinic_id": str(clinic_id),
        }
    )


@pytest.fixture
def sample_brief(clinic_id: uuid.UUID) -> AIBrief:
    brief = MagicMock(spec=AIBrief)
    brief.id = uuid.uuid4()
    brief.clinic_id = clinic_id
    brief.date = dt.date(2026, 11, 1)
    brief.body_md = "## Nightly Operations Summary\n- 45 patients served today."
    brief.anomalies = [{"type": "high_wait", "doctor": "Dr. Tariq", "wait_min": 52}]
    brief.feedback = None
    brief.created_at = dt.datetime.now(dt.UTC)
    return brief


@pytest.mark.asyncio
async def test_owner_can_get_daily_brief(owner_token: str, sample_brief: AIBrief) -> None:
    """Acceptance test: Owner can fetch daily brief for their clinic (F-018)."""
    with patch("app.services.ai_service.AIService.get_daily_brief") as mock_get:
        mock_get.return_value = sample_brief

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get(
                "/api/v1/ai/daily-brief?date=2026-11-01",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["body_md"] == sample_brief.body_md
        assert len(data["anomalies"]) == 1
        assert data["anomalies"][0]["type"] == "high_wait"


@pytest.mark.asyncio
async def test_owner_can_generate_daily_brief(owner_token: str, sample_brief: AIBrief) -> None:
    """Acceptance test: Owner can trigger on-demand brief generation (F-018)."""
    with patch("app.services.ai_service.AIService.generate_daily_brief") as mock_gen:
        mock_gen.return_value = sample_brief

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                "/api/v1/ai/daily-brief/generate?date=2026-11-01",
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["body_md"] == sample_brief.body_md


@pytest.mark.asyncio
async def test_owner_can_submit_feedback(owner_token: str, sample_brief: AIBrief) -> None:
    """Acceptance test: Owner can rate brief with thumbs up/down (F-018)."""
    sample_brief.feedback = "up"
    with patch("app.services.ai_service.AIService.submit_brief_feedback") as mock_fb:
        mock_fb.return_value = sample_brief

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                f"/api/v1/ai/daily-brief/{sample_brief.id}/feedback",
                json={"feedback": "up"},
                headers={"Authorization": f"Bearer {owner_token}"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["feedback"] == "up"


@pytest.mark.asyncio
async def test_doctor_forbidden_from_daily_brief(doctor_token: str) -> None:
    """Acceptance test: Doctor cannot access owner daily brief."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/ai/daily-brief",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_daily_brief_job_endpoint() -> None:
    """Acceptance test: Scheduled job triggers daily brief batch execution (W-010)."""
    with patch("app.services.jobs.JobsService.run_daily_brief") as mock_job:
        from app.schemas.jobs import DailyBriefJobResponse

        mock_job.return_value = DailyBriefJobResponse(
            success=True,
            date=dt.date(2026, 11, 1),
            clinics_processed=3,
            briefs_generated=3,
            errors=[],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(
                "/api/v1/jobs/daily-brief",
                json={"date": "2026-11-01"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["clinics_processed"] == 3
        assert data["briefs_generated"] == 3
