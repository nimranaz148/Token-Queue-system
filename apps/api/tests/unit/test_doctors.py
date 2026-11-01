import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.doctor import Doctor
from app.schemas.auth import Role

client = TestClient(app)


def make_auth_headers(role: str, clinic_id: uuid.UUID | None = None) -> dict[str, str]:
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "email": f"{role.lower()}@example.com",
            "role": role,
            "clinic_id": str(clinic_id) if clinic_id else None,
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


def test_list_doctors_permissions(mock_db: AsyncMock) -> None:
    # 1. Unauthenticated -> 401
    res = client.get("/api/v1/doctors")
    assert res.status_code == 401

    # 2. No clinic_id in token -> 403
    headers_no_clinic = make_auth_headers(Role.OWNER, clinic_id=None)
    res_no_clinic = client.get("/api/v1/doctors", headers=headers_no_clinic)
    assert res_no_clinic.status_code == 403

    # 3. Clinic staff (Owner, Doctor, Reception) can list
    clinic_id = uuid.uuid4()
    for role in [Role.OWNER, Role.DOCTOR, Role.RECEPTION]:
        headers = make_auth_headers(role, clinic_id=clinic_id)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        res_staff = client.get("/api/v1/doctors", headers=headers)
        assert res_staff.status_code == 200
        assert res_staff.json() == {"items": [], "total": 0}


def test_create_doctor_owner_only(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    payload = {
        "name": "Dr. Sarah Khan",
        "specialty": "Pediatrics",
        "daily_online_limit": 25,
        "consult_minutes": 15,
        "active": True,
        "schedules": [
            {"weekday": 0, "start_time": "09:00", "end_time": "13:00"},
            {"weekday": 2, "start_time": "14:00", "end_time": "18:00"},
        ],
    }

    # Doctor role cannot create -> 403
    doc_headers = make_auth_headers(Role.DOCTOR, clinic_id=clinic_id)
    res_doc = client.post("/api/v1/doctors", json=payload, headers=doc_headers)
    assert res_doc.status_code == 403

    # Reception role cannot create -> 403
    rec_headers = make_auth_headers(Role.RECEPTION, clinic_id=clinic_id)
    res_rec = client.post("/api/v1/doctors", json=payload, headers=rec_headers)
    assert res_rec.status_code == 403

    # Owner can create -> 201
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)
    res_owner = client.post("/api/v1/doctors", json=payload, headers=owner_headers)
    assert res_owner.status_code == 201
    data = res_owner.json()
    assert data["name"] == "Dr. Sarah Khan"
    assert data["specialty"] == "Pediatrics"
    assert data["daily_online_limit"] == 25
    assert len(data["schedules"]) == 2
    assert mock_db.add.called
    assert mock_db.commit.called


def test_create_doctor_invalid_schedule_times(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    # End time before start time -> 422
    payload = {
        "name": "Dr. Invalid Schedule",
        "schedules": [
            {"weekday": 1, "start_time": "17:00", "end_time": "09:00"},
        ],
    }
    res = client.post("/api/v1/doctors", json=payload, headers=owner_headers)
    assert res.status_code == 422


def test_get_doctor_cross_clinic_404(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    # Doctor not found in this clinic tenant
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    res = client.get(f"/api/v1/doctors/{doctor_id}", headers=owner_headers)
    assert res.status_code == 404
    assert res.json()["code"] == "DOCTOR_NOT_FOUND"


def test_update_doctor_success(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    now = datetime.now(UTC)
    existing_doc = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Old Name",
        specialty="General",
        daily_online_limit=30,
        consult_minutes=10,
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_doc
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)
    res = client.patch(
        f"/api/v1/doctors/{doctor_id}",
        json={"name": "Dr. New Name", "active": False},
        headers=owner_headers,
    )
    assert res.status_code == 200
    assert existing_doc.name == "Dr. New Name"
    assert existing_doc.active is False
    assert mock_db.commit.called


def test_update_schedules_success(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    now = datetime.now(UTC)
    existing_doc = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Khan",
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_doc
    mock_db.execute.return_value = mock_result

    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)
    new_schedules = [
        {"weekday": 1, "start_time": "10:00", "end_time": "14:00"},
        {"weekday": 3, "start_time": "15:00", "end_time": "19:00"},
    ]
    res = client.put(
        f"/api/v1/doctors/{doctor_id}/schedule",
        json=new_schedules,
        headers=owner_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["weekday"] == 1
    assert data[0]["start_time"] == "10:00"
    assert data[0]["end_time"] == "14:00"


def test_delete_doctor_soft_deletes(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    now = datetime.now(UTC)
    existing_doc = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. To Delete",
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_doc
    mock_db.execute.return_value = mock_result

    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)
    res = client.delete(f"/api/v1/doctors/{doctor_id}", headers=owner_headers)
    assert res.status_code == 204
    assert existing_doc.deleted_at is not None
    assert existing_doc.active is False
    assert mock_db.commit.called
