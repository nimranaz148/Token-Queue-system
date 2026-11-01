import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import create_access_token
from app.main import app
from app.models.clinic import Clinic, ClinicSettings
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser, Role
from app.schemas.settings import ClinicSettingsUpdate
from app.services.settings import SettingsService


@pytest.mark.asyncio
async def test_get_settings_success():
    """Verify GET settings returns full operational and clinic fields (F-011)."""
    clinic_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    mock_clinic = Clinic(
        id=clinic_id,
        name="Shifa Care",
        slug="shifa-care",
        time_zone="Asia/Karachi",
        address="123 Hospital Road",
        phone="+923001234567",
        maps_url="https://maps.google.com/?q=shifa",
        logo_path="/logos/shifa.png",
    )

    mock_settings = ClinicSettings(
        clinic_id=clinic_id,
        online_booking_enabled=True,
        daily_online_limit=50,
        advance_days=1,
        default_consult_minutes=15,
        call_only_arrived=False,
        language_default="en",
        share_advice_with_patient=True,
        ai_notes_enabled=False,
        version=1,
        updated_at=now,
    )

    session = AsyncMock(spec=AsyncSession)
    mock_res = MagicMock()
    mock_res.first.return_value = (mock_clinic, mock_settings)
    session.execute.return_value = mock_res

    current_owner = CurrentUser(
        user_id=user_id,
        email="owner@example.com",
        name="Dr. Tariq",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )

    service = SettingsService(session)
    result = await service.get_settings(clinic_id=clinic_id, current_user=current_owner)

    assert result.clinic_id == clinic_id
    assert result.clinic_name == "Shifa Care"
    assert result.online_booking_enabled is True
    assert result.daily_online_limit == 50
    assert result.default_consult_minutes == 15
    assert result.share_advice_with_patient is True
    assert result.version == 1


@pytest.mark.asyncio
async def test_update_settings_and_audit():
    """Verify PUT settings updates values, increments version, and records audit trail."""
    clinic_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(UTC)

    mock_clinic = Clinic(
        id=clinic_id,
        name="Shifa Care",
        slug="shifa-care",
        time_zone="Asia/Karachi",
    )
    mock_settings = ClinicSettings(
        clinic_id=clinic_id,
        online_booking_enabled=True,
        daily_online_limit=50,
        advance_days=1,
        default_consult_minutes=10,
        call_only_arrived=False,
        language_default="en",
        share_advice_with_patient=False,
        ai_notes_enabled=False,
        version=1,
        updated_at=now,
    )

    session = AsyncMock(spec=AsyncSession)
    mock_res = MagicMock()
    mock_res.first.return_value = (mock_clinic, mock_settings)
    session.execute.return_value = mock_res

    current_owner = CurrentUser(
        user_id=user_id,
        email="owner@example.com",
        name="Owner User",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )

    update_payload = ClinicSettingsUpdate(
        version=1,
        clinic_name="Shifa Care Super Clinic",
        online_booking_enabled=False,
        daily_online_limit=75,
        default_consult_minutes=20,
        share_advice_with_patient=True,
        ai_notes_enabled=True,
    )

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        service = SettingsService(session)
        updated = await service.update_settings(
            clinic_id=clinic_id,
            payload=update_payload,
            current_user=current_owner,
        )

        assert updated.clinic_name == "Shifa Care Super Clinic"
        assert updated.online_booking_enabled is False
        assert updated.daily_online_limit == 75
        assert updated.default_consult_minutes == 20
        assert updated.share_advice_with_patient is True
        assert updated.ai_notes_enabled is True
        assert updated.version == 2
        assert mock_settings.ai_consent_accepted_by == user_id
        assert mock_settings.ai_consent_accepted_at is not None

        # Audit verification
        assert mock_audit.call_count == 1
        audit_call = mock_audit.call_args.kwargs
        assert audit_call["action"] == AuditAction.SETTINGS_CHANGE
        assert audit_call["entity"] == "clinic_settings"
        assert audit_call["before"]["version"] == 1
        assert audit_call["after"]["version"] == 2
        assert audit_call["after"]["online_booking_enabled"] is False


@pytest.mark.asyncio
async def test_update_settings_optimistic_locking_conflict():
    """Outdated version must raise 409 Conflict (SETTINGS_VERSION_CONFLICT)."""
    clinic_id = uuid.uuid4()
    mock_clinic = Clinic(id=clinic_id, name="Test Clinic", slug="test-clinic")
    mock_settings = ClinicSettings(
        clinic_id=clinic_id,
        version=5,  # Current version is 5
        updated_at=datetime.now(UTC),
    )

    session = AsyncMock(spec=AsyncSession)
    mock_res = MagicMock()
    mock_res.first.return_value = (mock_clinic, mock_settings)
    session.execute.return_value = mock_res

    current_owner = CurrentUser(
        user_id=uuid.uuid4(),
        email="owner@example.com",
        name="Owner User",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )

    # Submitted version is 4 (stale)
    update_payload = ClinicSettingsUpdate(
        version=4,
        daily_online_limit=100,
    )

    service = SettingsService(session)
    with pytest.raises(AppException) as exc:
        await service.update_settings(
            clinic_id=clinic_id,
            payload=update_payload,
            current_user=current_owner,
        )

    assert exc.value.status_code == 409
    assert exc.value.code == "SETTINGS_VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_settings_api_endpoint_rbac():
    """Verify GET and PUT /api/v1/settings RBAC enforcement."""
    clinic_id = str(uuid.uuid4())

    owner_token = create_access_token(
        {"sub": str(uuid.uuid4()), "role": Role.OWNER, "clinic_id": clinic_id, "type": "access"}
    )
    doctor_token = create_access_token(
        {"sub": str(uuid.uuid4()), "role": Role.DOCTOR, "clinic_id": clinic_id, "type": "access"}
    )
    reception_token = create_access_token(
        {"sub": str(uuid.uuid4()), "role": Role.RECEPTION, "clinic_id": clinic_id, "type": "access"}
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Doctor gets 403 Forbidden
        res_doc = await client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert res_doc.status_code == 403

        # 2. Reception gets 403 Forbidden
        res_rec = await client.get(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {reception_token}"},
        )
        assert res_rec.status_code == 403

        # 3. Owner gets 200 OK
        mock_clinic = Clinic(
            id=uuid.UUID(clinic_id),
            name="Shifa",
            slug="shifa",
            time_zone="Asia/Karachi",
        )
        mock_settings = ClinicSettings(
            clinic_id=uuid.UUID(clinic_id),
            online_booking_enabled=True,
            daily_online_limit=50,
            advance_days=1,
            default_consult_minutes=10,
            call_only_arrived=False,
            language_default="en",
            share_advice_with_patient=False,
            ai_notes_enabled=False,
            version=1,
            updated_at=datetime.now(UTC),
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_res = MagicMock()
        mock_res.first.return_value = (mock_clinic, mock_settings)
        mock_session.execute.return_value = mock_res

        async def override_get_db():
            yield mock_session

        app.dependency_overrides[get_db] = override_get_db
        try:
            res_owner = await client.get(
                "/api/v1/settings",
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            assert res_owner.status_code == 200
            data = res_owner.json()
            assert data["clinic_name"] == "Shifa"
            assert data["online_booking_enabled"] is True
            assert data["version"] == 1
        finally:
            app.dependency_overrides.pop(get_db, None)
