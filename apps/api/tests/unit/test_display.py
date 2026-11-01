import hashlib
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.main import app
from app.models.clinic import Clinic
from app.models.display import DisplayDevice
from app.models.doctor import Doctor
from app.schemas.auth import CurrentUser, Role
from app.services.display import _PAIRING_STORE


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def clinic_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def doctor_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def owner_user(clinic_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="owner@clinic.com",
        name="Owner",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )


@pytest.fixture
def doctor_user(clinic_id: uuid.UUID, doctor_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="doctor@clinic.com",
        name="Doctor",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
    )


def test_initiate_pairing_forbidden_for_doctor(
    test_client: TestClient,
    doctor_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        res = test_client.post(
            "/api/v1/display/pairing/initiate",
            json={"device_name": "Waiting Room TV", "doctor_ids": [str(doctor_id)]},
        )
        assert res.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_initiate_and_complete_pairing_lifecycle(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    owner_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: owner_user
    try:
        mock_session = AsyncMock()
        doc_exec = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [doctor_id]
        doc_exec.scalars.return_value = mock_scalars

        mock_session.execute.return_value = doc_exec
        app.dependency_overrides[get_db] = lambda: mock_session

        # 1. Owner initiates pairing
        res = test_client.post(
            "/api/v1/display/pairing/initiate",
            json={"device_name": "Waiting Room TV", "doctor_ids": [str(doctor_id)]},
        )
        assert res.status_code == 201
        data = res.json()
        pairing_code = data["pairing_code"]
        assert len(pairing_code) == 6
        assert "expires_at" in data

        # 2. TV Screen submits pairing code
        mock_clinic = Clinic(id=clinic_id, name="Shifa Clinic", slug="shifa")
        clinic_exec = MagicMock()
        clinic_exec.scalar_one_or_none.return_value = mock_clinic
        mock_session.execute.return_value = clinic_exec

        with patch("app.services.display.AuditService.record_audit") as mock_audit:
            res_complete = test_client.post(
                "/api/v1/display/pairing/complete",
                json={"pairing_code": pairing_code},
            )
            assert res_complete.status_code == 200
            comp_data = res_complete.json()
            assert "device_token" in comp_data
            assert comp_data["clinic_name"] == "Shifa Clinic"
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()
            mock_audit.assert_called_once()
            assert mock_audit.call_args[1]["action"] == "display.pair"
    finally:
        _PAIRING_STORE.clear()
        app.dependency_overrides.clear()


def test_get_display_feed_exposes_token_numbers_only_zero_phi(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> None:
    mock_session = AsyncMock()
    raw_token = "secret_tv_device_token_123"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    mock_device = DisplayDevice(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        name="Main Waiting TV",
        token_hash=token_hash,
        doctor_ids=[str(doctor_id)],
        paired_at=datetime.now(UTC),
        revoked_at=None,
    )
    mock_doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Ayesha", active=True)

    # Tokens in queue today: 1 serving (#12), 2 arrived (#13, #14)
    tokens_data = [
        (12, "serving", 1),
        (13, "arrived", 2),
        (14, "booked", 3),
    ]

    dev_exec = MagicMock()
    dev_exec.scalar_one_or_none.return_value = mock_device

    clinic_name_exec = MagicMock()
    clinic_name_exec.scalar_one_or_none.return_value = "Al-Shifa Family Clinic"

    doc_exec = MagicMock()
    doc_scalars = MagicMock()
    doc_scalars.all.return_value = [mock_doctor]
    doc_exec.scalars.return_value = doc_scalars

    tok_exec = MagicMock()
    tok_exec.all.return_value = tokens_data

    mock_session.execute.side_effect = [dev_exec, clinic_name_exec, doc_exec, tok_exec]
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        res = test_client.get(
            "/api/v1/display/feed",
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert res.status_code == 200
        feed = res.json()
        assert feed["clinic_name"] == "Al-Shifa Family Clinic"
        assert len(feed["doctors"]) == 1
        d_feed = feed["doctors"][0]
        assert d_feed["doctor_name"] == "Dr. Ayesha"
        assert d_feed["current_token"] == 12
        assert d_feed["next_tokens"] == [13, 14]

        # Crucial security assertion (PRD Rule 10): NO patient names or phones anywhere in feed
        raw_text = res.text
        assert "patient" not in raw_text.lower()
        assert "phone" not in raw_text.lower()
    finally:
        app.dependency_overrides.clear()


def test_get_display_feed_unauthorized_when_revoked(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
) -> None:
    mock_session = AsyncMock()
    raw_token = "revoked_tv_token"

    # Device is not returned because it is revoked
    dev_exec = MagicMock()
    dev_exec.scalar_one_or_none.return_value = None

    mock_session.execute.return_value = dev_exec
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        res = test_client.get(
            "/api/v1/display/feed",
            headers={"Authorization": f"Bearer {raw_token}"},
        )
        assert res.status_code == 401
    finally:
        app.dependency_overrides.clear()
