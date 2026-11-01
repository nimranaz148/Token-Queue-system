import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.main import app
from app.models.clinic import ClinicSettings
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.visit import Visit
from app.schemas.auth import CurrentUser, Role


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
def patient_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def doctor_user(clinic_id: uuid.UUID, doctor_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="doctor@clinic.com",
        name="Dr. Tariq",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
    )


@pytest.fixture
def reception_user(clinic_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )


def test_get_patient_history_forbidden_for_reception(
    test_client: TestClient,
    patient_id: uuid.UUID,
    reception_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: reception_user
    try:
        res = test_client.get(f"/api/v1/visits/patient/{patient_id}")
        assert res.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_get_patient_history_success_for_doctor(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        mock_session = AsyncMock()
        mock_patient = Patient(
            id=patient_id,
            clinic_id=clinic_id,
            name="Muhammad Usman",
            phone="+923001234567",
            date_of_birth=date(1990, 1, 1),
            gender="male",
        )
        mock_settings = ClinicSettings(
            clinic_id=clinic_id,
            share_advice_with_patient=True,
        )
        mock_doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Tariq", active=True)
        mock_visit = Visit(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            complaint="Severe cough and chest congestion",
            notes="Chest sounds clear, no wheezing",
            medicines_advice="Syrup Acefyl 2 tsp TDS, Panadol 500mg SOS",
            share_with_patient=True,
            created_at=datetime.now(UTC),
        )

        p_exec = MagicMock()
        p_exec.scalar_one_or_none.return_value = mock_patient

        s_exec = MagicMock()
        s_exec.scalar_one_or_none.return_value = mock_settings

        v_exec = MagicMock()
        v_exec.all.return_value = [(mock_visit, mock_doctor, None)]

        mock_session.execute.side_effect = [p_exec, s_exec, v_exec]
        app.dependency_overrides[get_db] = lambda: mock_session

        res = test_client.get(f"/api/v1/visits/patient/{patient_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["patient_name"] == "Muhammad Usman"
        assert data["share_advice_clinic_setting"] is True
        assert len(data["visits"]) == 1
        assert data["visits"][0]["complaint"] == "Severe cough and chest congestion"
        assert data["visits"][0]["medicines_advice"] == "Syrup Acefyl 2 tsp TDS, Panadol 500mg SOS"
    finally:
        app.dependency_overrides.clear()


def test_create_visit_note_success_and_audited(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    doctor_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        mock_session = AsyncMock()
        mock_patient = Patient(
            id=patient_id,
            clinic_id=clinic_id,
            name="Zahra Bibi",
            phone="+923009998877",
        )
        mock_doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Tariq", active=True)

        p_exec = MagicMock()
        p_exec.scalar_one_or_none.return_value = mock_patient

        d_exec = MagicMock()
        d_exec.scalar_one_or_none.return_value = mock_doctor

        mock_session.execute.side_effect = [p_exec, d_exec]
        app.dependency_overrides[get_db] = lambda: mock_session

        payload = {
            "patient_id": str(patient_id),
            "complaint": "Headache and fatigue",
            "notes": "Patient advised hydration",
            "medicines_advice": "Paracetamol 500mg 1 tab TDS",
            "share_with_patient": True,
        }

        with patch("app.services.visit.AuditService.record_audit") as mock_audit:
            res = test_client.post("/api/v1/visits", json=payload)
            assert res.status_code == 201
            data = res.json()
            assert data["complaint"] == "Headache and fatigue"
            assert data["medicines_advice"] == "Paracetamol 500mg 1 tab TDS"
            mock_session.add.assert_called()
            mock_session.commit.assert_awaited()
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs["action"] == "visit.create"
    finally:
        app.dependency_overrides.clear()


def test_create_visit_note_validation_lengths(
    test_client: TestClient,
    patient_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        # Complaint exceeds 500 chars
        payload = {
            "patient_id": str(patient_id),
            "complaint": "C" * 501,
        }
        res = test_client.post("/api/v1/visits", json=payload)
        assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()
