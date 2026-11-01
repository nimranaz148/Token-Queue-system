import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.main import app
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.stats import DailyStats
from app.models.token import Token
from app.schemas.audit import AuditAction
from app.services.jobs import JobsService


@pytest.mark.asyncio
async def test_day_close_transitions_and_daily_stats_w006():
    """W-006 Day Close: unserved -> no_show, serving -> done, daily_stats upserted, idempotent."""
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    today = date.today()
    now = datetime.now(UTC)

    mock_clinic = Clinic(
        id=clinic_id,
        name="Shifa Care Clinic",
        slug="shifa-care",
        status="active",
        time_zone="Asia/Karachi",
    )

    mock_doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Tariq",
        active=True,
    )

    t_booked = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=1,
        position=Decimal("1.0"),
        source="online",
        status="booked",
        public_code="code-1",
        created_at=now - timedelta(hours=3),
    )

    t_arrived = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=2,
        position=Decimal("2.0"),
        source="walk_in",
        status="arrived",
        public_code="code-2",
        arrived_at=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2),
    )

    t_serving = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=3,
        position=Decimal("3.0"),
        source="walk_in",
        status="serving",
        public_code="code-3",
        called_at=now - timedelta(minutes=20),
        arrived_at=now - timedelta(minutes=40),
        created_at=now - timedelta(hours=1),
    )

    t_done = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=4,
        position=Decimal("4.0"),
        source="online",
        status="done",
        public_code="code-4",
        called_at=now - timedelta(hours=1),
        completed_at=now - timedelta(minutes=45),
        created_at=now - timedelta(hours=2),
    )

    session = AsyncMock(spec=AsyncSession)

    def execute_side_effect(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)

        if "FROM clinics" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_clinic
            mock_result.scalars.return_value.all.return_value = [mock_clinic]
        elif "FROM tokens" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [
                t_booked,
                t_arrived,
                t_serving,
                t_done,
            ]
        elif "FROM doctors" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [mock_doctor]
        elif "FROM daily_stats" in stmt_str:
            # First run: no existing stats
            mock_result.scalar_one_or_none.return_value = None
        else:
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
        return mock_result

    session.execute.side_effect = execute_side_effect

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        service = JobsService(session)
        response = await service.run_day_close(clinic_id=clinic_id, target_date=today, force=True)

        assert response.success is True
        assert response.processed_count == 1
        res = response.results[0]
        assert res.tokens_no_show == 2  # t_booked, t_arrived
        assert res.tokens_done == 1  # t_serving -> done

        # Check token states
        assert t_booked.status == "no_show"
        assert t_arrived.status == "no_show"
        assert t_serving.status == "done"
        assert t_serving.completed_at is not None
        assert t_done.status == "done"

        # Check daily stats
        doc_stat = res.doctor_stats[0]
        assert doc_stat.doctor_id == doctor_id
        assert doc_stat.seen == 2  # t_done and t_serving newly done
        assert doc_stat.no_shows == 2  # t_booked and t_arrived
        assert doc_stat.online_count == 2
        assert doc_stat.walk_in_count == 2

        # Check audit calls occurred
        assert mock_audit.call_count >= 3
        actions = [call.kwargs.get("action") for call in mock_audit.call_args_list]
        assert AuditAction.TOKEN_NO_SHOW in actions
        assert AuditAction.TOKEN_NEXT in actions


@pytest.mark.asyncio
async def test_day_close_idempotency():
    """W-006: Running day close multiple times on the same clinic/date updates existing DailyStats."""
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    today = date.today()

    mock_clinic = Clinic(
        id=clinic_id,
        name="Iqra Health",
        slug="iqra-health",
        status="active",
        time_zone="Asia/Karachi",
    )
    mock_doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Bilal", active=True)

    # Tokens already in terminal states
    t_no_show = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=today,
        number=1,
        position=Decimal("1.0"),
        source="online",
        status="no_show",
        public_code="code-done-1",
    )
    t_done = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=today,
        number=2,
        position=Decimal("2.0"),
        source="walk_in",
        status="done",
        public_code="code-done-2",
    )

    existing_stat = DailyStats(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        date=today,
        seen=1,
        no_shows=1,
        cancelled=0,
        online_count=1,
        walk_in_count=1,
    )

    session = AsyncMock(spec=AsyncSession)

    def execute_side_effect(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "FROM clinics" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_clinic
        elif "FROM tokens" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [t_no_show, t_done]
        elif "FROM doctors" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [mock_doctor]
        elif "FROM daily_stats" in stmt_str:
            mock_result.scalar_one_or_none.return_value = existing_stat
        return mock_result

    session.execute.side_effect = execute_side_effect

    service = JobsService(session)
    response = await service.run_day_close(clinic_id=clinic_id, target_date=today, force=True)

    assert response.success is True
    res = response.results[0]
    assert res.tokens_no_show == 0  # None transitioned
    assert res.tokens_done == 0  # None transitioned
    # existing_stat updated in place
    assert existing_stat.seen == 1
    assert existing_stat.no_shows == 1


@pytest.mark.asyncio
async def test_day_close_api_endpoint_authentication():
    """Verify POST /api/v1/jobs/day-close security and header validation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. With production env, invalid token must return 401
        with patch.object(settings, "environment", "production"):
            res = await client.post(
                "/api/v1/jobs/day-close",
                headers={"Authorization": "Bearer bad-token"},
            )
            assert res.status_code == 401

        # 2. With valid service token header, authentication succeeds
        with (
            patch.object(settings, "environment", "production"),
            patch.object(settings, "jobs_service_token", "secret-test-token"),
            patch("app.services.jobs.JobsService.run_day_close") as mock_run,
        ):
            from app.schemas.jobs import DayCloseResponse

            mock_run.return_value = DayCloseResponse(success=True, processed_count=0, results=[])

            res = await client.post(
                "/api/v1/jobs/day-close",
                headers={"Authorization": "Bearer secret-test-token"},
                json={"force": True},
            )
            assert res.status_code == 200
            assert res.json()["success"] is True
