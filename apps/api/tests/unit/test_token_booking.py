import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.errors import AppException
from app.core.phone import normalize_phone
from app.main import app
from app.models.clinic import Clinic
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.token import Token, TokenCounter
from app.schemas.token import TokenBookingRequest
from app.services.token import TokenService

client = TestClient(app)


@pytest.fixture
def mock_db() -> Generator[AsyncMock, None, None]:
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield session
    app.dependency_overrides.pop(get_db, None)


def test_phone_normalization_e164() -> None:
    """Acceptance test: Phone normalisation to E.164 (Task 29)."""
    assert normalize_phone("03001234567") == "+923001234567"
    assert normalize_phone("+92 300 1234567") == "+923001234567"
    assert normalize_phone("0300-1234567") == "+923001234567"
    assert normalize_phone("3001234567") == "+923001234567"
    assert normalize_phone("+923001234567") == "+923001234567"

    # Rejection of invalid phones
    with pytest.raises(AppException) as exc_info:
        normalize_phone("123")
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "INVALID_PHONE"

    with pytest.raises(AppException) as exc_info2:
        normalize_phone("abcdefghijk")
    assert exc_info2.value.status_code == 422


@pytest.mark.asyncio
async def test_booking_assigns_next_sequence_number_per_doctor_per_day() -> None:
    """Acceptance test: Booking assigns the next sequence number per doctor per day (Task 29)."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    today = date.today()

    clinic = Clinic(id=clinic_id, name="City Health Clinic", slug="city-health", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Tariq Khan",
        active=True,
        daily_online_limit=30,
        consult_minutes=15,
    )
    schedule = DoctorSchedule(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        weekday=today.weekday(),
        start_time=time(9, 0),
        end_time=time(14, 0),
    )

    counter = TokenCounter(
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        visit_date=today,
        last_number=0,
    )

    # Mock DB query executions
    # 1. clinic -> clinic
    # 2. settings -> None
    # 3. doctor -> doctor
    # 4. schedule -> schedule
    # 5. any_sched_stmt count -> 1
    # 6. active count -> 0
    # 7. patient -> None
    # 8. counter -> counter
    exec_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=schedule)))
        ),
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalar=MagicMock(return_value=0)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=counter)),
    ]
    session.execute = AsyncMock(side_effect=exec_results)

    service = TokenService(session)
    payload = TokenBookingRequest(
        doctor_id=doctor_id,
        visit_date=today,
        patient_name="Ahmed Ali",
        phone="03001234567",
        turnstile_token="1x0000000000000000000000000000000AA",
    )

    result = await service.book_token(slug="city-health", payload=payload)

    assert result.number == 1
    assert result.status == "booked"
    assert result.source == "online"
    assert result.doctor_name == "Dr. Tariq Khan"
    assert result.clinic_slug == "city-health"
    assert len(result.public_code) >= 16
    assert counter.last_number == 1


@pytest.mark.asyncio
async def test_daily_online_limit_blocks_with_409() -> None:
    """Acceptance test: Daily online limit blocks with 409 (Task 29)."""
    session = AsyncMock()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    today = date.today()

    clinic = Clinic(id=clinic_id, name="City Health Clinic", slug="city-health", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Tariq Khan",
        active=True,
        daily_online_limit=10,
    )
    schedule = DoctorSchedule(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        weekday=today.weekday(),
        start_time=time(9, 0),
        end_time=time(14, 0),
    )

    exec_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=schedule)))
        ),
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalar=MagicMock(return_value=10)),  # limit reached: 10/10
    ]
    session.execute = AsyncMock(side_effect=exec_results)

    service = TokenService(session)
    payload = TokenBookingRequest(
        doctor_id=doctor_id,
        visit_date=today,
        patient_name="Hamza Khan",
        phone="03001234567",
        turnstile_token="1x0000000000000000000000000000000AA",
    )

    with pytest.raises(AppException) as exc_info:
        await service.book_token(slug="city-health", payload=payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DAILY_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_active_duplicate_blocks_with_409_and_existing_link() -> None:
    """Acceptance test: Active duplicate blocks with 409 and existing link (Task 29)."""
    session = AsyncMock()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    today = date.today()

    clinic = Clinic(id=clinic_id, name="City Health Clinic", slug="city-health", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Tariq Khan",
        active=True,
        daily_online_limit=50,
    )
    schedule = DoctorSchedule(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        weekday=today.weekday(),
        start_time=time(9, 0),
        end_time=time(14, 0),
    )
    patient = Patient(
        id=patient_id,
        clinic_id=clinic_id,
        phone="+923001234567",
        name="Hamza Khan",
    )
    existing_token = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        visit_date=today,
        number=5,
        public_code="existing-code-123456",
        status="booked",
    )

    exec_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=schedule)))
        ),
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalar=MagicMock(return_value=4)),  # active count 4
        MagicMock(scalar_one_or_none=MagicMock(return_value=patient)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=existing_token)),
    ]
    session.execute = AsyncMock(side_effect=exec_results)

    service = TokenService(session)
    payload = TokenBookingRequest(
        doctor_id=doctor_id,
        visit_date=today,
        patient_name="Hamza Khan",
        phone="03001234567",
        turnstile_token="1x0000000000000000000000000000000AA",
    )

    with pytest.raises(AppException) as exc_info:
        await service.book_token(slug="city-health", payload=payload)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "ACTIVE_TOKEN_EXISTS"
    assert exc_info.value.extra.get("existing_public_code") == "existing-code-123456"
    assert exc_info.value.extra.get("existing_token_url") == "/t/existing-code-123456"


@pytest.mark.asyncio
async def test_turnstile_failure_rejects() -> None:
    """Acceptance test: Turnstile failure rejects (Task 29)."""
    session = AsyncMock()
    service = TokenService(session)
    today = date.today()

    payload = TokenBookingRequest(
        doctor_id=uuid.uuid4(),
        visit_date=today,
        patient_name="Bot Patient",
        phone="03001234567",
        turnstile_token="2x0000000000000000000000000000000AA",  # official fail token
    )

    with pytest.raises(AppException) as exc_info:
        await service.book_token(slug="city-health", payload=payload)

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "TURNSTILE_FAILED"


def test_public_tokens_api_route(mock_db: AsyncMock) -> None:
    """Test public endpoint POST /api/v1/public/clinics/{slug}/tokens via FastAPI client."""
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    today = date.today()

    clinic = Clinic(id=clinic_id, name="City Health Clinic", slug="city-health", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Tariq Khan",
        active=True,
        daily_online_limit=20,
    )
    schedule = DoctorSchedule(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        weekday=today.weekday(),
        start_time=time(9, 0),
        end_time=time(14, 0),
    )
    counter = TokenCounter(
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        visit_date=today,
        last_number=1,
    )

    exec_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=schedule)))
        ),
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalar=MagicMock(return_value=1)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=counter)),
    ]
    mock_db.execute.side_effect = exec_results

    res = client.post(
        "/api/v1/public/clinics/city-health/tokens",
        json={
            "doctor_id": str(doctor_id),
            "visit_date": str(today),
            "patient_name": "Zubair Ahmad",
            "phone": "03001234567",
            "turnstile_token": "1x0000000000000000000000000000000AA",
        },
    )

    assert res.status_code == 201
    data = res.json()
    assert data["number"] == 2
    assert data["status"] == "booked"
    assert data["doctor_name"] == "Dr. Tariq Khan"
    assert data["clinic_slug"] == "city-health"
