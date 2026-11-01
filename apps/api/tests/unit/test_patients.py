import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.main import app
from app.models.patient import Patient
from app.schemas.auth import CurrentUser, Role


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def clinic_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def patient_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def reception_user(clinic_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="reception@clinic.com",
        name="Receptionist",
        role=Role.RECEPTION,
        clinic_id=clinic_id,
    )


@pytest.fixture
def owner_user(clinic_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="owner@clinic.com",
        name="Clinic Owner",
        role=Role.OWNER,
        clinic_id=clinic_id,
    )


@pytest.fixture
def doctor_user(clinic_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        user_id=uuid.uuid4(),
        email="doctor@clinic.com",
        name="Dr. Khan",
        role=Role.DOCTOR,
        clinic_id=clinic_id,
    )


def test_search_patients_requires_auth(test_client: TestClient) -> None:
    res = test_client.get("/api/v1/patients?query=Usman")
    assert res.status_code == 401


def test_search_patients_query_less_than_two_chars_returns_empty(
    test_client: TestClient,
    reception_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: reception_user
    try:
        mock_session = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_session

        res = test_client.get("/api/v1/patients?query=U")
        assert res.status_code == 200
        assert res.json() == []
        mock_session.execute.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_search_patients_success_for_staff(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    reception_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: reception_user
    try:
        mock_session = AsyncMock()
        mock_patient = Patient(
            id=patient_id,
            clinic_id=clinic_id,
            name="Muhammad Usman",
            phone="+923001234567",
            date_of_birth=date(1990, 5, 15),
            gender="male",
            notes="Regular checkups",
        )

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_patient]
        patient_exec_res = MagicMock()
        patient_exec_res.scalars.return_value = mock_scalars

        visit_exec_res = MagicMock()
        visit_exec_res.all.return_value = [(patient_id, 3, date(2026, 10, 20))]

        mock_session.execute.side_effect = [patient_exec_res, visit_exec_res, MagicMock()]
        app.dependency_overrides[get_db] = lambda: mock_session

        res = test_client.get("/api/v1/patients?query=Usman")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "Muhammad Usman"
        assert data[0]["phone"] == "+923001234567"
        assert data[0]["visit_count"] == 3
        assert data[0]["last_visit_date"] == "2026-10-20"
    finally:
        app.dependency_overrides.clear()


def test_get_patient_profile_success(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        mock_session = AsyncMock()
        mock_patient = Patient(
            id=patient_id,
            clinic_id=clinic_id,
            name="Fatima Bibi",
            phone="+923009876543",
            date_of_birth=date(1985, 2, 10),
            gender="female",
            notes="Allergic to penicillin",
            created_at=datetime.now(UTC),
            updated_at=None,
        )

        patient_exec_res = MagicMock()
        patient_exec_res.scalar_one_or_none.return_value = mock_patient

        visit_exec_res = MagicMock()
        visit_exec_res.first.return_value = (5, date(2026, 11, 1))

        mock_session.execute.side_effect = [patient_exec_res, visit_exec_res]
        app.dependency_overrides[get_db] = lambda: mock_session

        res = test_client.get(f"/api/v1/patients/{patient_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(patient_id)
        assert data["name"] == "Fatima Bibi"
        assert data["notes"] == "Allergic to penicillin"
        assert data["visit_count"] == 5
        assert data["last_visit_date"] == "2026-11-01"
    finally:
        app.dependency_overrides.clear()


def test_update_patient_profile_by_reception_updates_and_audits(
    test_client: TestClient,
    clinic_id: uuid.UUID,
    patient_id: uuid.UUID,
    reception_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: reception_user
    try:
        mock_session = AsyncMock()
        mock_patient = Patient(
            id=patient_id,
            clinic_id=clinic_id,
            name="Ali Khan",
            phone="+923001112233",
            date_of_birth=date(1995, 1, 1),
            gender="male",
            notes=None,
            created_at=datetime.now(UTC),
            updated_at=None,
        )

        exec_res_get = MagicMock()
        exec_res_get.scalar_one_or_none.return_value = mock_patient

        visit_res = MagicMock()
        visit_res.first.return_value = (1, date(2026, 10, 15))

        mock_session.execute.side_effect = [exec_res_get, exec_res_get, visit_res]
        app.dependency_overrides[get_db] = lambda: mock_session

        update_payload = {
            "name": "Ali Khan Updated",
            "phone": "03001112233",
            "date_of_birth": "1995-01-01",
            "gender": "male",
            "notes": "Updated contact info and notes",
        }

        with patch("app.services.patient.AuditService.record_audit") as mock_audit:
            res = test_client.put(f"/api/v1/patients/{patient_id}", json=update_payload)
            assert res.status_code == 200
            assert mock_patient.name == "Ali Khan Updated"
            assert mock_patient.phone == "+923001112233"
            assert mock_patient.notes == "Updated contact info and notes"
            mock_session.commit.assert_awaited()
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            assert call_kwargs["entity"] == "patient"
            assert call_kwargs["entity_id"] == patient_id
            assert call_kwargs["action"] == "patient.edit"
    finally:
        app.dependency_overrides.clear()


def test_update_patient_profile_by_doctor_forbidden(
    test_client: TestClient,
    patient_id: uuid.UUID,
    doctor_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: doctor_user
    try:
        res = test_client.put(
            f"/api/v1/patients/{patient_id}",
            json={
                "name": "Updated Name",
                "phone": "+923001112233",
            },
        )
        assert res.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_update_patient_profile_rejects_future_dob(
    test_client: TestClient,
    patient_id: uuid.UUID,
    reception_user: CurrentUser,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: reception_user
    try:
        future_date = (date.today() + timedelta(days=10)).isoformat()
        res = test_client.put(
            f"/api/v1/patients/{patient_id}",
            json={
                "name": "Baby Child",
                "phone": "+923001112233",
                "date_of_birth": future_date,
            },
        )
        assert res.status_code == 422
    finally:
        app.dependency_overrides.clear()
