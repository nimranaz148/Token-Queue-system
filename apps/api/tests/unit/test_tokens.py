import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import create_access_token
from app.main import app
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.token import Token
from app.schemas.auth import CurrentUser, Role
from app.services.token import TokenService

client = TestClient(app)


def make_auth_headers(
    role: str,
    clinic_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
) -> dict[str, str]:
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "email": f"{role}@example.com",
            "role": role,
            "clinic_id": str(clinic_id) if clinic_id else None,
            "doctor_id": str(doctor_id) if doctor_id else None,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_db() -> Generator[AsyncMock, None, None]:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield session
    app.dependency_overrides.pop(get_db, None)


def test_list_tokens_permissions(mock_db: AsyncMock) -> None:
    """Acceptance: reception, owner, doctor(own) can access; unauthorized get 401 or 403."""
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    other_doc_id = uuid.uuid4()

    # 1. Unauthenticated -> 401
    res_unauth = client.get("/api/v1/tokens")
    assert res_unauth.status_code == 401

    # 2. Reception -> 200
    with patch.object(TokenService, "list_reception_tokens", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([], 0)
        rec_headers = make_auth_headers(Role.RECEPTION, clinic_id=clinic_id)
        res_rec = client.get("/api/v1/tokens", headers=rec_headers)
        assert res_rec.status_code == 200
        assert res_rec.json() == {"items": [], "total": 0, "date": date.today().isoformat()}

    # 3. Owner -> 200
    with patch.object(TokenService, "list_reception_tokens", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([], 0)
        own_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)
        res_own = client.get("/api/v1/tokens", headers=own_headers)
        assert res_own.status_code == 200

    # 4. Doctor accessing own queue -> 200
    with patch.object(TokenService, "list_reception_tokens", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ([], 0)
        doc_headers = make_auth_headers(Role.DOCTOR, clinic_id=clinic_id, doctor_id=doc_id)
        res_doc = client.get("/api/v1/tokens", headers=doc_headers)
        assert res_doc.status_code == 200

    # 5. Doctor accessing another doctor's queue -> 403
    doc_headers = make_auth_headers(Role.DOCTOR, clinic_id=clinic_id, doctor_id=doc_id)
    res_other = client.get(f"/api/v1/tokens?doctor_id={other_doc_id}", headers=doc_headers)
    assert res_other.status_code == 403
    assert res_other.json()["code"] == "FORBIDDEN_DOCTOR_QUEUE"

    # 6. Unauthorized role -> 403
    patient_headers = make_auth_headers("patient", clinic_id=clinic_id)
    res_bad = client.get("/api/v1/tokens", headers=patient_headers)
    assert res_bad.status_code == 403


@pytest.mark.asyncio
async def test_token_service_list_reception_tokens_filtering_and_masking() -> None:
    """Acceptance: Validation and field specs match F-004 in PRD §5.3.

    - phone masked except last 4 digits (***4567)
    - doctor, status, search filtering
    """
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    session = AsyncMock()

    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )

    doctor = Doctor(id=doc_id, clinic_id=clinic_id, name="Dr. Bilal", active=True)
    patient = Patient(id=uuid.uuid4(), clinic_id=clinic_id, name="Ali Khan", phone="+923001234567")
    token = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient.id,
        visit_date=date.today(),
        number=7,
        position=Decimal(7),
        source="online",
        status="booked",
        public_code="code-123456789012345678",
        created_at=datetime.now(UTC),
    )

    # Mock count execute and rows execute
    mock_count_res = MagicMock()
    mock_count_res.scalar.return_value = 1

    mock_rows_res = MagicMock()
    mock_rows_res.all.return_value = [(token, patient, doctor)]

    session.execute = AsyncMock(side_effect=[mock_count_res, mock_rows_res])

    service = TokenService(session)
    items, total = await service.list_reception_tokens(
        clinic_id=clinic_id,
        current_user=current_user,
        target_date=date.today(),
        doctor_id=doc_id,
        status_filter=["booked"],
        search="Ali",
    )

    assert total == 1
    assert len(items) == 1
    item = items[0]
    assert item.number == 7
    assert item.patient_name == "Ali Khan"
    # Masked except last 4 digits
    assert item.phone == "***4567"
    assert item.source == "online"
    assert item.status == "booked"
    assert item.doctor_name == "Dr. Bilal"


@pytest.mark.asyncio
async def test_token_service_mark_arrived_rules_and_transitions() -> None:
    """Acceptance: Row action mark_arrived only allowed from 'booked', writes audit and event rows."""
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    token_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )

    doctor = Doctor(id=doc_id, clinic_id=clinic_id, name="Dr. Bilal", active=True)
    patient = Patient(id=uuid.uuid4(), clinic_id=clinic_id, name="Ali Khan", phone="+923001234567")

    # 1. Non-staff role raises 403
    doc_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="doc@clinic.com",
        name="Dr. Bilal",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
        doctor_id=doc_id,
    )
    service = TokenService(session)
    with pytest.raises(AppException) as exc_info:
        await service.mark_token_arrived(clinic_id, token_id, doc_user)
    assert exc_info.value.code == "FORBIDDEN"

    # 2. Token already arrived -> invalid status transition 400
    already_arrived_token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient.id,
        visit_date=date.today(),
        number=7,
        position=Decimal(7),
        source="online",
        status="arrived",
        public_code="code-already-arrived",
        created_at=datetime.now(UTC),
    )
    mock_res_arrived = MagicMock()
    mock_res_arrived.one_or_none.return_value = (already_arrived_token, patient, doctor)
    session.execute = AsyncMock(return_value=mock_res_arrived)

    with pytest.raises(AppException) as exc_info:
        await service.mark_token_arrived(clinic_id, token_id, current_user)
    assert exc_info.value.code == "INVALID_STATUS_TRANSITION"

    # 3. Valid transition from 'booked' -> 'arrived'
    booked_token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient.id,
        visit_date=date.today(),
        number=7,
        position=Decimal(7),
        source="online",
        status="booked",
        public_code="code-booked-token",
        created_at=datetime.now(UTC),
    )
    mock_res_booked = MagicMock()
    mock_res_booked.one_or_none.return_value = (booked_token, patient, doctor)
    session.execute = AsyncMock(return_value=mock_res_booked)

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        res = await service.mark_token_arrived(clinic_id, token_id, current_user)

    assert res.status == "arrived"
    assert res.arrived_at is not None
    assert booked_token.status == "arrived"
    # Check token_events added
    session.add.assert_called()
    session.commit.assert_awaited()
    # Check realtime broadcast triggered
    mock_instance.broadcast_queue_update.assert_awaited()


@pytest.mark.asyncio
async def test_token_service_cancel_by_staff_rules() -> None:
    """Acceptance: Cancel action requires reason (>= 2 chars), transitions to cancelled, and audits."""
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    token_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )

    doctor = Doctor(id=doc_id, clinic_id=clinic_id, name="Dr. Bilal", active=True)
    patient = Patient(id=uuid.uuid4(), clinic_id=clinic_id, name="Ali Khan", phone="+923001234567")
    token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient.id,
        visit_date=date.today(),
        number=7,
        position=Decimal(7),
        source="online",
        status="booked",
        public_code="code-to-cancel",
        created_at=datetime.now(UTC),
    )

    service = TokenService(session)

    # 1. Missing reason -> 400
    with pytest.raises(AppException) as exc_info:
        await service.cancel_token_by_staff(clinic_id, token_id, " ", current_user)
    assert exc_info.value.code == "REASON_REQUIRED"

    # 2. Token already done -> 409 Conflict
    token.status = "done"
    mock_res = MagicMock()
    mock_res.one_or_none.return_value = (token, patient, doctor)
    session.execute = AsyncMock(return_value=mock_res)

    with pytest.raises(AppException) as exc_info:
        await service.cancel_token_by_staff(
            clinic_id, token_id, "Patient was not available", current_user
        )
    assert exc_info.value.code == "CANNOT_CANCEL"

    # 3. Valid cancellation
    token.status = "booked"
    mock_res.one_or_none.return_value = (token, patient, doctor)

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        res = await service.cancel_token_by_staff(
            clinic_id, token_id, "Patient requested reschedule", current_user
        )

    assert res.status == "cancelled"
    assert res.cancelled_reason == "Patient requested reschedule"
    assert token.status == "cancelled"
    session.add.assert_called()
    session.commit.assert_awaited()
