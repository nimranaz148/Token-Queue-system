import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.errors import AppException
from app.main import app
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.token import Token
from app.services.token import TokenService

client = TestClient(app)


@pytest.fixture
def mock_db() -> Generator[AsyncMock, None, None]:
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield session
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_token_confirm_details_success() -> None:
    """Acceptance test: Retrieve token details for F-002 Token Confirm (Task 30)."""
    session = AsyncMock()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    token_id = uuid.uuid4()
    now = datetime.now(UTC)

    token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=18,
        position=Decimal(18),
        source="online",
        status="booked",
        public_code="pub-code-confirm-18",
        estimated_at=now,
        created_at=now,
        updated_at=now,
    )
    clinic = Clinic(id=clinic_id, name="Shifa Clinic", slug="shifa-clinic", status="active")
    doctor = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Sarah Tariq",
        specialty="Pediatrics",
        active=True,
    )

    # 1. token -> token
    # 2. clinic -> clinic
    # 3. doctor -> doctor
    # 4. ahead count -> 3
    # 5. serving -> 14
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=token)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
            MagicMock(scalar=MagicMock(return_value=3)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=14)),
        ]
    )

    service = TokenService(session)
    result = await service.get_token_by_public_code("pub-code-confirm-18")

    assert result.number == 18
    assert result.doctor_name == "Dr. Sarah Tariq"
    assert result.specialty == "Pediatrics"
    assert result.clinic_name == "Shifa Clinic"
    assert result.people_ahead == 3
    assert result.estimated_wait_minutes == 30
    assert result.current_serving_number == 14
    assert result.status == "booked"


@pytest.mark.asyncio
async def test_get_token_confirm_not_found() -> None:
    """Acceptance test: Non-existent public code returns 404 (Task 30)."""
    session = AsyncMock()
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )

    service = TokenService(session)
    with pytest.raises(AppException) as exc_info:
        await service.get_token_by_public_code("non-existent-code")

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "TOKEN_NOT_FOUND"


@pytest.mark.asyncio
async def test_cancel_token_success() -> None:
    """Acceptance test: Patient cancels booked token (W-005, Task 30)."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    token = Token(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=18,
        position=Decimal(18),
        source="online",
        status="booked",
        public_code="pub-code-confirm-18",
    )
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=token))
    )

    service = TokenService(session)
    result = await service.cancel_token_by_public_code("pub-code-confirm-18")

    assert result.status == "cancelled"
    assert token.status == "cancelled"
    assert token.cancelled_reason == "Cancelled by patient"


@pytest.mark.asyncio
async def test_cancel_serving_or_done_token_fails_with_409() -> None:
    """Acceptance test: Cancelling a token that is serving or done fails with 409 (Task 30)."""
    session = AsyncMock()
    token = Token(
        id=uuid.uuid4(),
        clinic_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=18,
        position=Decimal(18),
        source="online",
        status="serving",
        public_code="pub-code-confirm-18",
    )
    session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=token))
    )

    service = TokenService(session)
    with pytest.raises(AppException) as exc_info:
        await service.cancel_token_by_public_code("pub-code-confirm-18")

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "CANNOT_CANCEL"


def test_public_tokens_confirm_and_cancel_endpoints(mock_db: AsyncMock) -> None:
    """Test GET and POST cancel endpoints via FastAPI test client (Task 30)."""
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    token_id = uuid.uuid4()
    now = datetime.now(UTC)

    token = Token(
        id=token_id,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=uuid.uuid4(),
        visit_date=date.today(),
        number=7,
        position=Decimal(7),
        source="online",
        status="booked",
        public_code="xyz-code-777",
        estimated_at=now,
        created_at=now,
        updated_at=now,
    )
    clinic = Clinic(id=clinic_id, name="Test Clinic", slug="test-clinic", status="active")
    doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Bilal", active=True)

    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=token)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=clinic)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=doctor)),
        MagicMock(scalar=MagicMock(return_value=2)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=5)),
    ]

    res_get = client.get("/api/v1/public/tokens/xyz-code-777")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["number"] == 7
    assert data["doctor_name"] == "Dr. Bilal"
    assert data["people_ahead"] == 2
    assert data["current_serving_number"] == 5

    # Cancel endpoint
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=token)),
    ]
    res_cancel = client.post("/api/v1/public/tokens/xyz-code-777/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"
