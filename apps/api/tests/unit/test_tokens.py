import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import create_access_token
from app.main import app
from app.models.clinic import ClinicSettings
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.token import Token
from app.models.visit import Visit
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


def test_create_walk_in_token_permissions(mock_db: AsyncMock) -> None:
    """Acceptance: Reception and owner can create walk-in tokens; others get 403."""
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    payload = {
        "doctor_id": str(doc_id),
        "patient_name": "Hamza Ali",
        "phone": "+923001234567",
        "ignore_daily_limit": False,
    }

    # 1. Reception -> 201
    with patch.object(TokenService, "create_walk_in_token", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {
            "id": uuid.uuid4(),
            "number": 10,
            "public_code": "walkin-public-code",
            "status": "arrived",
            "source": "walk_in",
            "patient_id": uuid.uuid4(),
            "patient_name": "Hamza Ali",
            "phone": "+923001234567",
            "doctor_id": doc_id,
            "doctor_name": "Dr. Tariq",
            "visit_date": date.today(),
            "position": 10.0,
            "arrived_at": datetime.now(UTC),
            "created_at": datetime.now(UTC),
        }
        rec_headers = make_auth_headers(Role.RECEPTION, clinic_id=clinic_id)
        res_rec = client.post("/api/v1/tokens", json=payload, headers=rec_headers)
        assert res_rec.status_code == 201
        assert res_rec.json()["number"] == 10
        assert res_rec.json()["status"] == "arrived"
        assert res_rec.json()["source"] == "walk_in"

    # 2. Doctor -> 403
    doc_headers = make_auth_headers(Role.DOCTOR, clinic_id=clinic_id, doctor_id=doc_id)
    res_doc = client.post("/api/v1/tokens", json=payload, headers=doc_headers)
    assert res_doc.status_code == 403

    # 3. Patient / non-staff -> 403
    unauth_headers = make_auth_headers("patient", clinic_id=clinic_id)
    res_unauth = client.post("/api/v1/tokens", json=payload, headers=unauth_headers)
    assert res_unauth.status_code == 403


@pytest.mark.asyncio
async def test_create_walk_in_token_field_validation_and_rules() -> None:
    """Acceptance: Field spec validation for F-005 in PRD §5.3:

    - patient_name (2-60 chars)
    - phone (E.164 normalization)
    - doctor with OPD today
    - ignore_daily_limit enforcement
    - result: token_number, read-only large
    """
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    current_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )

    doctor = Doctor(
        id=doc_id,
        clinic_id=clinic_id,
        name="Dr. Tariq",
        active=True,
        daily_online_limit=5,
    )
    today = date.today()
    schedule = DoctorSchedule(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doc_id,
        weekday=today.weekday(),
        start_time=datetime.strptime("09:00", "%H:%M").time(),
        end_time=datetime.strptime("13:00", "%H:%M").time(),
    )

    service = TokenService(session)

    # 1. Inactive doctor / not found -> 422 DOCTOR_UNAVAILABLE
    mock_res_doc_none = MagicMock()
    mock_res_doc_none.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=mock_res_doc_none)

    from app.schemas.token import WalkInTokenCreateRequest

    with pytest.raises(AppException) as exc_info:
        await service.create_walk_in_token(
            clinic_id,
            WalkInTokenCreateRequest(
                doctor_id=doc_id,
                patient_name="Hamza",
                phone="+923001234567",
            ),
            current_user,
        )
    assert exc_info.value.code == "DOCTOR_UNAVAILABLE"

    # 2. Doctor has no OPD today -> 422 DOCTOR_NO_OPD_TODAY
    mock_res_doc = MagicMock()
    mock_res_doc.scalar_one_or_none.return_value = doctor
    mock_res_sched_none = MagicMock()
    mock_res_sched_none.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(side_effect=[mock_res_doc, mock_res_sched_none])

    with pytest.raises(AppException) as exc_info:
        await service.create_walk_in_token(
            clinic_id,
            WalkInTokenCreateRequest(
                doctor_id=doc_id,
                patient_name="Hamza",
                phone="+923001234567",
            ),
            current_user,
        )
    assert exc_info.value.code == "DOCTOR_NO_OPD_TODAY"

    # 3. Daily limit reached and ignore_daily_limit is False -> 409 DAILY_LIMIT_REACHED
    mock_res_sched = MagicMock()
    mock_res_sched.scalar_one_or_none.return_value = schedule
    mock_res_count = MagicMock()
    mock_res_count.scalar.return_value = 5  # limit is 5
    session.execute = AsyncMock(side_effect=[mock_res_doc, mock_res_sched, mock_res_count])

    with pytest.raises(AppException) as exc_info:
        await service.create_walk_in_token(
            clinic_id,
            WalkInTokenCreateRequest(
                doctor_id=doc_id,
                patient_name="Hamza",
                phone="+923001234567",
                ignore_daily_limit=False,
            ),
            current_user,
        )
    assert exc_info.value.code == "DAILY_LIMIT_REACHED"

    # 4. Successful creation with ignore_daily_limit=True (overrides limit, stores token)
    mock_res_counter = MagicMock()
    mock_res_counter.scalar_one_or_none.return_value = None  # creates counter starting at 1
    mock_res_patient = MagicMock()
    mock_res_patient.scalar_one_or_none.return_value = None  # new patient

    session.execute = AsyncMock(
        side_effect=[
            mock_res_doc,
            mock_res_sched,
            mock_res_patient,
            mock_res_counter,
            mock_res_counter,
        ]
    )

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        res = await service.create_walk_in_token(
            clinic_id,
            WalkInTokenCreateRequest(
                doctor_id=doc_id,
                patient_name="Hamza Usman",
                phone="03001234567",
                ignore_daily_limit=True,
            ),
            current_user,
        )

    assert res.number == 1
    assert res.status == "arrived"
    assert res.source == "walk_in"
    assert res.patient_name == "Hamza Usman"
    assert res.phone == "+923001234567"  # normalized to E.164
    session.add.assert_called()
    session.commit.assert_awaited()
    mock_instance.broadcast_queue_update.assert_awaited()


@pytest.mark.asyncio
async def test_doctor_panel_queue_and_actions() -> None:
    """Test Doctor Panel F-007: queue retrieval, next patient, skip, hold, and recall."""
    session = AsyncMock(spec=AsyncSession)
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    patient_1 = Patient(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        name="Muhammad Ali",
        phone="+923001111111",
        date_of_birth=date(1990, 1, 1),
        gender="male",
    )
    patient_2 = Patient(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        name="Sara Khan",
        phone="+923002222222",
        date_of_birth=date(2000, 6, 15),
        gender="female",
    )
    doctor = Doctor(id=doc_id, clinic_id=clinic_id, name="Dr. Ayesha", active=True)

    doc_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="doctor@clinic.com",
        name="Dr. Ayesha",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
        doctor_id=doc_id,
    )
    reception_user = CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )

    service = TokenService(session)

    # 1. Non-doctor/non-owner gets 403 on queue
    with pytest.raises(AppException) as exc_info:
        await service.get_doctor_queue(clinic_id, doc_id, date.today(), reception_user)
    assert exc_info.value.code == "FORBIDDEN"

    # 2. Get Doctor Queue success
    tok_serving = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient_1.id,
        visit_date=date.today(),
        number=1,
        position=Decimal("1.00"),
        source="online",
        status="serving",
        public_code="code-doc-1",
        created_at=datetime.now(UTC),
    )
    tok_arrived = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=patient_2.id,
        visit_date=date.today(),
        number=2,
        position=Decimal("2.00"),
        source="walk_in",
        status="arrived",
        public_code="code-doc-2",
        created_at=datetime.now(UTC),
    )

    mock_doc_res = MagicMock()
    mock_doc_res.scalar_one_or_none.return_value = doctor
    mock_tokens_res = MagicMock()
    mock_tokens_res.all.return_value = [
        (tok_serving, patient_1),
        (tok_arrived, patient_2),
    ]

    session.execute = AsyncMock(side_effect=[mock_doc_res, mock_tokens_res])

    q_res = await service.get_doctor_queue(clinic_id, doc_id, date.today(), doc_user)
    assert q_res.doctor_id == doc_id
    assert q_res.doctor_name == "Dr. Ayesha"
    assert q_res.current_token is not None
    assert q_res.current_token.number == 1
    assert q_res.current_token.patient_name == "Muhammad Ali"
    assert q_res.current_token.patient_age is not None
    assert len(q_res.next_tokens) == 1
    assert q_res.next_tokens[0].number == 2
    assert q_res.counts["serving"] == 1
    assert q_res.counts["arrived"] == 1

    # 3. Call NEXT patient advances current to done and next to serving
    mock_tokens_res_next = MagicMock()
    mock_tokens_res_next.all.return_value = [
        (tok_serving, patient_1),
        (tok_arrived, patient_2),
    ]
    session.execute = AsyncMock(return_value=mock_tokens_res_next)

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        next_res = await service.call_next_patient(
            clinic_id,
            doc_id,
            quick_note="Patient showed mild fever, advised rest",
            current_user=doc_user,
        )

    assert next_res.success is True
    assert tok_serving.status == "done"
    assert tok_serving.completed_at is not None
    assert tok_arrived.status == "serving"
    assert tok_arrived.called_at is not None
    session.commit.assert_awaited()
    mock_instance.broadcast_queue_update.assert_awaited()

    # 4. Skip currently serving patient
    mock_skip_res = MagicMock()
    mock_skip_res.first.return_value = (tok_arrived, patient_2)
    session.execute = AsyncMock(return_value=mock_skip_res)

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        skip_res = await service.skip_current_patient(clinic_id, doc_id, doc_user)

    assert skip_res.success is True
    assert tok_arrived.status == "skipped"
    session.commit.assert_awaited()

    # 5. Recall skipped patient back to arrived
    mock_tok_recall = MagicMock()
    mock_tok_recall.first.return_value = (tok_arrived, patient_2)
    mock_min_pos = MagicMock()
    mock_min_pos.scalar_one_or_none.return_value = Decimal("2.00")

    session.execute = AsyncMock(side_effect=[mock_tok_recall, mock_min_pos])

    with patch("app.services.token.SupabaseRealtimeClient") as mock_realtime:
        mock_instance = AsyncMock()
        mock_realtime.return_value = mock_instance
        recall_res = await service.recall_patient(clinic_id, doc_id, tok_arrived.id, doc_user)

    assert recall_res.success is True
    assert tok_arrived.status == "arrived"
    assert tok_arrived.position < Decimal("2.00")  # placed before min
    session.commit.assert_awaited()
    mock_instance.broadcast_queue_update.assert_awaited()


@pytest.mark.asyncio
async def test_doctor_ki_hidayat_shared_advice_f021() -> None:
    """Test F-021 Doctor ki Hidayat: advice visible only if clinic setting ON and visit allows (<= 30 days)."""
    session = AsyncMock(spec=AsyncSession)
    clinic_id = uuid.uuid4()
    doc_id = uuid.uuid4()
    doctor = Doctor(id=doc_id, clinic_id=clinic_id, name="Dr. Tariq Khan", active=True)
    token = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doc_id,
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=19,
        position=Decimal("19.00"),
        source="online",
        status="done",
        public_code="hidayat-code-19",
        created_at=datetime.now(UTC),
    )

    service = TokenService(session)

    # 1. Clinic setting OFF -> returns unshared message "Clinic se rabta karein"
    mock_tok_res = MagicMock()
    mock_tok_res.first.return_value = (token, doctor)

    mock_set_off = MagicMock()
    mock_set_off.scalar_one_or_none.return_value = ClinicSettings(
        clinic_id=clinic_id, share_advice_with_patient=False
    )

    session.execute = AsyncMock(side_effect=[mock_tok_res, mock_set_off])

    res_off = await service.get_shared_visit_advice("hidayat-code-19")
    assert res_off.shared is False
    assert res_off.message == "Clinic se rabta karein"
    assert res_off.medicines_advice is None

    # 2. Clinic setting ON and Visit share_with_patient = True and <= 30 days old
    mock_tok_res2 = MagicMock()
    mock_tok_res2.first.return_value = (token, doctor)

    mock_set_on = MagicMock()
    mock_set_on.scalar_one_or_none.return_value = ClinicSettings(
        clinic_id=clinic_id, share_advice_with_patient=True
    )

    visit = Visit(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        patient_id=token.patient_id,
        doctor_id=doc_id,
        token_id=token.id,
        complaint="Private: Sore throat",
        notes="Private: Mild pharyngitis",
        medicines_advice="Tab Azomax 500mg OD for 3 days, Gargles TDS",
        share_with_patient=True,
        created_at=datetime.now(UTC) - timedelta(days=2),
    )
    mock_vis = MagicMock()
    mock_vis.scalar_one_or_none.return_value = visit

    session.execute = AsyncMock(side_effect=[mock_tok_res2, mock_set_on, mock_vis])

    res_on = await service.get_shared_visit_advice("hidayat-code-19")
    assert res_on.shared is True
    assert res_on.doctor_name == "Dr. Tariq Khan"
    assert res_on.medicines_advice == "Tab Azomax 500mg OD for 3 days, Gargles TDS"
    # Security: Ensure notes and complaint are never present in model
    assert not hasattr(res_on, "notes")
    assert not hasattr(res_on, "complaint")

    # 3. Visit older than 30 days -> returns unshared message
    old_visit = Visit(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        patient_id=token.patient_id,
        doctor_id=doc_id,
        token_id=token.id,
        medicines_advice="Expired advice",
        share_with_patient=True,
        created_at=datetime.now(UTC) - timedelta(days=35),
    )
    mock_tok_res3 = MagicMock()
    mock_tok_res3.first.return_value = (token, doctor)
    mock_vis_old = MagicMock()
    mock_vis_old.scalar_one_or_none.return_value = old_visit

    session.execute = AsyncMock(side_effect=[mock_tok_res3, mock_set_on, mock_vis_old])

    res_old = await service.get_shared_visit_advice("hidayat-code-19")
    assert res_old.shared is False
    assert res_old.message == "Clinic se rabta karein"
