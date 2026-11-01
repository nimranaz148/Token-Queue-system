import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import AppException
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.token import Token
from app.services.token import TokenService


@pytest.mark.asyncio
async def test_live_queue_metrics_and_people_ahead() -> None:
    """Acceptance test: F-003 Live queue correctly computes people ahead and estimated wait minutes (Task 31)."""
    session = AsyncMock()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    token_id = uuid.uuid4()
    now = datetime.now(UTC)

    my_token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=18,
        position=Decimal(18),
        source="online",
        status="booked",
        public_code="live-code-18",
        estimated_at=now,
        created_at=now,
        updated_at=now,
    )
    clinic = Clinic(id=clinic_id, name="Aapka Clinic", slug="aapka-clinic", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Mansoor",
        specialty="General OPD",
        active=True,
        consult_minutes=12,
    )

    # 1. token -> my_token
    # 2. clinic -> clinic
    # 3. doctor -> doctor
    # 4. ahead count -> 5
    # 5. serving -> 12
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=my_token)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
            MagicMock(scalar=MagicMock(return_value=5)),  # 5 people ahead
            MagicMock(scalar_one_or_none=MagicMock(return_value=12)),  # current serving #12
        ]
    )

    service = TokenService(session)
    result = await service.get_token_by_public_code("live-code-18")

    assert result.number == 18
    assert result.current_serving_number == 12
    assert result.people_ahead == 5
    assert result.estimated_wait_minutes == 60  # 5 people * 12 min
    assert result.doctor_name == "Dr. Mansoor"
    assert result.clinic_name == "Aapka Clinic"


@pytest.mark.asyncio
async def test_live_queue_zero_people_ahead() -> None:
    """Acceptance test: Next in line has zero people ahead and 0 min wait (Task 31)."""
    session = AsyncMock()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    now = datetime.now(UTC)

    my_token = Token(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=1,
        position=Decimal(1),
        source="online",
        status="booked",
        public_code="live-code-1",
        estimated_at=now,
        created_at=now,
        updated_at=now,
    )
    clinic = Clinic(id=clinic_id, name="Aapka Clinic", slug="aapka-clinic", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Mansoor",
        active=True,
        consult_minutes=15,
    )

    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=my_token)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
            MagicMock(scalar=MagicMock(return_value=0)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]
    )

    service = TokenService(session)
    result = await service.get_token_by_public_code("live-code-1")

    assert result.number == 1
    assert result.people_ahead == 0
    assert result.estimated_wait_minutes == 0


@pytest.mark.asyncio
async def test_live_queue_invalid_code_raises_404() -> None:
    """Acceptance test: Accessing live queue with invalid code returns 404 (Task 31)."""
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    service = TokenService(session)
    with pytest.raises(AppException) as exc_info:
        await service.get_token_by_public_code("invalid-code")

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "TOKEN_NOT_FOUND"
