import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.ai import AIRun
from app.models.clinic import Clinic
from app.models.token import Token
from app.schemas.auth import Role
from app.services.admin_overview import AdminOverviewService


@pytest.mark.asyncio
async def test_admin_overview_kpis_and_seeded_computation():
    """Verify D-002 KPIs: active clinics, tokens today/7d, idle clinics, AI spend on seeded dataset."""
    today = dt.date.today()
    now_utc = dt.datetime.now(dt.UTC)
    c1_id = uuid.uuid4()
    c2_id = uuid.uuid4()
    c3_id = uuid.uuid4()

    # Clinic 1: Active, active tokens
    c1 = Clinic(
        id=c1_id,
        name="Shifa Active Clinic",
        slug="shifa-active",
        status="active",
        created_at=now_utc - dt.timedelta(days=10),
        updated_at=now_utc - dt.timedelta(days=10),
    )
    # Clinic 2: Active, idle (no tokens in last 3 days)
    c2 = Clinic(
        id=c2_id,
        name="Al-Razi Idle Clinic",
        slug="al-razi-idle",
        status="active",
        created_at=now_utc - dt.timedelta(days=20),
        updated_at=now_utc - dt.timedelta(days=20),
    )
    # Clinic 3: Trial, idle (0 tokens ever)
    c3 = Clinic(
        id=c3_id,
        name="Trial Clinic",
        slug="trial-clinic",
        status="trial",
        created_at=now_utc - dt.timedelta(days=5),
        updated_at=now_utc - dt.timedelta(days=5),
    )

    # Seeded Tokens:
    # 2 tokens today for c1
    # 3 tokens 5 days ago for c1
    # Total tokens today = 2
    # Total tokens 7d = 5
    # Idle clinics = c2 (0 tokens in 3d) + c3 (0 tokens in 3d) = 2
    # Active clinics = c1 + c2 = 2
    t1 = Token(
        id=uuid.uuid4(),
        clinic_id=c1_id,
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        visit_date=today,
        number=1,
        position=Decimal("1.0"),
        source="online",
        status="booked",
        public_code="code-ov-1",
        created_at=now_utc - dt.timedelta(hours=2),
    )
    t2 = Token(
        id=uuid.uuid4(),
        clinic_id=c1_id,
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        visit_date=today,
        number=2,
        position=Decimal("2.0"),
        source="walk_in",
        status="arrived",
        public_code="code-ov-2",
        created_at=now_utc - dt.timedelta(hours=1),
    )
    t3 = Token(
        id=uuid.uuid4(),
        clinic_id=c1_id,
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        visit_date=today - dt.timedelta(days=5),
        number=3,
        position=Decimal("3.0"),
        source="online",
        status="done",
        public_code="code-ov-3",
        created_at=now_utc - dt.timedelta(days=5),
    )

    # AI Runs this month:
    # r1: $0.002400
    # r2: $0.001600
    # Total AI spend = $0.004000 -> $0.00 rounded
    r1 = AIRun(
        id=uuid.uuid4(),
        clinic_id=c1_id,
        feature="patient_chat",
        provider="openrouter",
        model="gpt-4o-mini",
        cost_usd=Decimal("0.002400"),
        status="success",
        at=now_utc - dt.timedelta(days=1),
    )
    r2 = AIRun(
        id=uuid.uuid4(),
        clinic_id=c1_id,
        feature="daily_brief",
        provider="gemini",
        model="gemini-1.5-flash",
        cost_usd=Decimal("0.001600"),
        status="success",
        at=now_utc - dt.timedelta(hours=5),
    )

    session = AsyncMock(spec=AsyncSession)

    def execute_side_effect(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "FROM clinics" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [c1, c2, c3]
        elif "FROM tokens" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [t1, t2, t3]
        elif "FROM ai_runs" in stmt_str:
            mock_result.scalars.return_value.all.return_value = [r1, r2]
        return mock_result

    session.execute.side_effect = execute_side_effect

    service = AdminOverviewService(session)
    res = await service.get_overview()

    assert res.kpis.active_clinics == 2
    assert res.kpis.total_clinics == 3
    assert res.kpis.tokens_today == 2
    assert res.kpis.tokens_7_days == 3
    assert res.kpis.idle_clinics == 2
    assert res.kpis.ai_spend_this_month == Decimal("0.00")
    assert len(res.clinics) == 3


@pytest.mark.asyncio
async def test_admin_overview_empty_dataset_handling():
    """An empty platform database must return clean zeroed KPIs and empty list without errors."""
    session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    service = AdminOverviewService(session)
    res = await service.get_overview()

    assert res.kpis.active_clinics == 0
    assert res.kpis.total_clinics == 0
    assert res.kpis.tokens_today == 0
    assert res.kpis.tokens_7_days == 0
    assert res.kpis.idle_clinics == 0
    assert res.kpis.ai_spend_this_month == Decimal("0.00")
    assert res.clinics == []


@pytest.mark.asyncio
async def test_admin_overview_rbac():
    """Only platform_admin role can access GET /api/v1/admin/overview."""
    admin_token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "role": Role.PLATFORM_ADMIN,
            "is_platform_admin": True,
            "type": "access",
        }
    )
    owner_token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "role": Role.OWNER,
            "clinic_id": str(uuid.uuid4()),
            "type": "access",
        }
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Owner receives 403 Forbidden
        res_owner = await client.get(
            "/api/v1/admin/overview",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert res_owner.status_code == 403

        # Platform Admin receives 200 OK
        mock_session = AsyncMock(spec=AsyncSession)
        mock_res = MagicMock()
        mock_res.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_res

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            res_admin = await client.get(
                "/api/v1/admin/overview",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert res_admin.status_code == 200
            data = res_admin.json()
            assert "kpis" in data
            assert "clinics" in data
        finally:
            app.dependency_overrides.pop(get_db, None)
