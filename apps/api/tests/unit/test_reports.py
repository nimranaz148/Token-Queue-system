import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import create_access_token
from app.main import app
from app.models.stats import DailyStats
from app.models.token import Token
from app.schemas.auth import CurrentUser, Role
from app.services.report import ReportService


@pytest.mark.asyncio
async def test_roz_ki_report_kpi_computation_f010():
    """Verify that each KPI on Roz ki Report (F-010 / D-001) matches hand-computed values."""
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    today = dt.date(2026, 11, 2)
    now = dt.datetime(2026, 11, 2, 12, 0, 0, tzinfo=dt.UTC)

    # Seeded tokens dataset:
    # 3 online (2 done, 1 no_show)
    # 2 walk-in (1 done, 1 cancelled)
    # Total tokens = 3 online + 2 walk-in = 5
    # Seen = 3
    # No-shows = 1
    # Cancelled = 1
    # Online share = 3 / 5 * 100 = 60.0%
    # Wait times:
    # t1: called at 10:20, arrived at 10:00 -> 20 min
    # t2: called at 10:50, arrived at 10:30 -> 20 min
    # t3: called at 11:30, arrived at 11:10 -> 20 min
    # Avg wait = 20.0 min

    t1 = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=1,
        position=Decimal("1.0"),
        source="online",
        status="done",
        public_code="code-r-1",
        arrived_at=now - dt.timedelta(minutes=120),
        called_at=now - dt.timedelta(minutes=100),
    )
    t2 = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=2,
        position=Decimal("2.0"),
        source="online",
        status="done",
        public_code="code-r-2",
        arrived_at=now - dt.timedelta(minutes=90),
        called_at=now - dt.timedelta(minutes=70),
    )
    t3 = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=3,
        position=Decimal("3.0"),
        source="walk_in",
        status="done",
        public_code="code-r-3",
        arrived_at=now - dt.timedelta(minutes=50),
        called_at=now - dt.timedelta(minutes=30),
    )
    t4 = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=4,
        position=Decimal("4.0"),
        source="online",
        status="no_show",
        public_code="code-r-4",
    )
    t5 = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=5,
        position=Decimal("5.0"),
        source="walk_in",
        status="cancelled",
        public_code="code-r-5",
    )

    # Doctor exists
    session = AsyncMock(spec=AsyncSession)

    def execute_side_effect(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "FROM daily_stats" in stmt_str:
            mock_result.scalars.return_value.all.return_value = []
        elif "FROM tokens" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [t1, t2, t3, t4, t5]
        elif "FROM doctors" in stmt_str:
            mock_result.scalar_one_or_none.return_value = "Dr. Farhan"
        return mock_result

    session.execute.side_effect = execute_side_effect

    current_owner = CurrentUser(
        user_id=uuid.uuid4(),
        email="owner@example.com",
        name="Owner User",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )

    service = ReportService(session)
    report = await service.get_daily_report(
        clinic_id=clinic_id,
        target_date=today,
        current_user=current_owner,
        doctor_id=doctor_id,
    )

    # Verification against hand-computed values:
    assert report.clinic_id == clinic_id
    assert report.date == today
    assert report.doctor_name == "Dr. Farhan"
    assert report.kpis.patients_seen == 3
    assert report.kpis.no_shows == 1
    assert report.kpis.cancelled_count == 1
    assert report.kpis.online_count == 3
    assert report.kpis.walk_in_count == 2
    assert report.kpis.total_tokens == 5
    assert report.kpis.online_share_pct == Decimal("60.0")
    assert report.kpis.avg_wait_minutes == Decimal("20.0")

    # Trend has exactly 7 days ending today
    assert len(report.trend_7_days) == 7
    assert report.trend_7_days[-1].date == today
    assert report.trend_7_days[-1].patients_seen == 3


@pytest.mark.asyncio
async def test_roz_ki_report_from_daily_stats_fast_path():
    """Verify that past days query DailyStats table directly for sub-second performance."""
    clinic_id = uuid.uuid4()
    past_date = dt.date(2026, 11, 1)

    stat = DailyStats(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=uuid.uuid4(),
        date=past_date,
        seen=54,
        no_shows=6,
        cancelled=2,
        online_count=20,
        walk_in_count=34,
        avg_wait_minutes=Decimal("14.00"),
        avg_consult_minutes=Decimal("8.50"),
    )

    session = AsyncMock(spec=AsyncSession)

    def execute_side_effect(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "FROM daily_stats" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [stat]
        return mock_result

    session.execute.side_effect = execute_side_effect

    current_owner = CurrentUser(
        user_id=uuid.uuid4(),
        email="owner@example.com",
        name="Owner User",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )

    service = ReportService(session)
    report = await service.get_daily_report(
        clinic_id=clinic_id,
        target_date=past_date,
        current_user=current_owner,
    )

    assert report.kpis.patients_seen == 54
    assert report.kpis.no_shows == 6
    assert report.kpis.total_tokens == 54
    assert report.kpis.avg_wait_minutes == Decimal("14.0")
    # 20 online / 54 total * 100 = 37.0%
    assert report.kpis.online_share_pct == Decimal("37.0")


@pytest.mark.asyncio
async def test_doctor_can_only_view_own_report():
    """A doctor requesting another doctor's report must receive 403 Forbidden."""
    clinic_id = uuid.uuid4()
    doc1_id = uuid.uuid4()
    doc2_id = uuid.uuid4()

    current_doc = CurrentUser(
        user_id=uuid.uuid4(),
        email="doctor@example.com",
        name="Dr. Tariq",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
        doctor_id=doc1_id,
    )

    session = AsyncMock(spec=AsyncSession)
    service = ReportService(session)

    # Attempt to request doc2's report
    with pytest.raises(AppException) as exc:
        await service.get_daily_report(
            clinic_id=clinic_id,
            target_date=dt.date.today(),
            current_user=current_doc,
            doctor_id=doc2_id,
        )

    assert exc.value.status_code == 403
    assert exc.value.code == "FORBIDDEN"


@pytest.mark.asyncio
async def test_reports_api_endpoint_rbac():
    """Verify GET /api/v1/reports/daily RBAC enforcement."""
    clinic_id = str(uuid.uuid4())

    owner_token = create_access_token(
        {"sub": str(uuid.uuid4()), "role": Role.OWNER, "clinic_id": clinic_id, "type": "access"}
    )
    reception_token = create_access_token(
        {"sub": str(uuid.uuid4()), "role": Role.RECEPTION, "clinic_id": clinic_id, "type": "access"}
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Reception gets 403 Forbidden
        res_rec = await client.get(
            "/api/v1/reports/daily",
            headers={"Authorization": f"Bearer {reception_token}"},
        )
        assert res_rec.status_code == 403

        # 2. Owner gets 200 OK (with mock db)
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            res_owner = await client.get(
                "/api/v1/reports/daily",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_owner.status_code == 200
            data = res_owner.json()
            assert "kpis" in data
            assert "trend_7_days" in data
        finally:
            app.dependency_overrides.pop(get_db, None)
