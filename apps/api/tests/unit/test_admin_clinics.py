import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.clinic import Clinic
from app.schemas.auth import Role

client = TestClient(app)


def make_auth_headers(role: str, is_admin: bool = False, clinic_id: uuid.UUID | None = None) -> dict[str, str]:
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "email": f"{role}@example.com",
            "role": role,
            "is_platform_admin": is_admin or role == Role.PLATFORM_ADMIN,
            "clinic_id": str(clinic_id) if clinic_id else None,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_mock_db() -> Generator[AsyncMock, None, None]:
    session = AsyncMock()
    session.add = MagicMock()

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield session
    app.dependency_overrides.pop(get_db, None)


def test_create_clinic_requires_platform_admin(admin_mock_db: AsyncMock) -> None:
    # 1. Unauthenticated request -> 401
    res = client.post("/api/v1/admin/clinics", json={"name": "Test Clinic", "slug": "test-clinic"})
    assert res.status_code == 401

    # 2. Doctor request -> 403
    doc_headers = make_auth_headers(Role.DOCTOR)
    res_doc = client.post(
        "/api/v1/admin/clinics",
        headers=doc_headers,
        json={"name": "Test Clinic", "slug": "test-clinic"},
    )
    assert res_doc.status_code == 403

    # 3. Reception request -> 403
    rec_headers = make_auth_headers(Role.RECEPTION)
    res_rec = client.post(
        "/api/v1/admin/clinics",
        headers=rec_headers,
        json={"name": "Test Clinic", "slug": "test-clinic"},
    )
    assert res_rec.status_code == 403


def test_create_clinic_success(admin_mock_db: AsyncMock) -> None:
    admin_headers = make_auth_headers(Role.PLATFORM_ADMIN, is_admin=True)

    # Mock slug check: slug doesn't exist yet
    mock_slug_res = MagicMock()
    mock_slug_res.scalar_one_or_none.return_value = None
    admin_mock_db.execute.return_value = mock_slug_res

    res = client.post(
        "/api/v1/admin/clinics",
        headers=admin_headers,
        json={
            "name": "Al-Rehman Clinic",
            "slug": "al-rehman",
            "address": "Ferozepur Road, Lahore",
            "phone": "03001234567",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Al-Rehman Clinic"
    assert data["slug"] == "al-rehman"
    assert data["status"] == "trial"
    assert "id" in data


def test_create_clinic_duplicate_slug_conflict(admin_mock_db: AsyncMock) -> None:
    admin_headers = make_auth_headers(Role.PLATFORM_ADMIN, is_admin=True)

    # Mock slug check: existing clinic found
    existing = Clinic(
        id=uuid.uuid4(),
        name="Existing",
        slug="al-rehman",
        time_zone="Asia/Karachi",
        created_at=datetime.now(UTC),
    )
    mock_slug_res = MagicMock()
    mock_slug_res.scalar_one_or_none.return_value = existing
    admin_mock_db.execute.return_value = mock_slug_res

    res = client.post(
        "/api/v1/admin/clinics",
        headers=admin_headers,
        json={"name": "Al-Rehman Clinic", "slug": "al-rehman"},
    )
    assert res.status_code == 409
    body = res.json()
    assert body["code"] == "SLUG_EXISTS"


def test_list_clinics_success(admin_mock_db: AsyncMock) -> None:
    admin_headers = make_auth_headers(Role.PLATFORM_ADMIN, is_admin=True)

    c1 = Clinic(
        id=uuid.uuid4(),
        name="Clinic Alpha",
        slug="clinic-alpha",
        status="trial",
        time_zone="Asia/Karachi",
        created_at=datetime.now(UTC),
    )
    c2 = Clinic(
        id=uuid.uuid4(),
        name="Clinic Beta",
        slug="clinic-beta",
        status="active",
        time_zone="Asia/Karachi",
        created_at=datetime.now(UTC),
    )

    mock_count = MagicMock()
    mock_count.scalar_one.return_value = 2

    mock_items = MagicMock()
    mock_items.scalars.return_value.all.return_value = [c1, c2]

    admin_mock_db.execute.side_effect = [mock_count, mock_items]

    res = client.get("/api/v1/admin/clinics?search=Clinic", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Clinic Alpha"


def test_update_clinic_status(admin_mock_db: AsyncMock) -> None:
    admin_headers = make_auth_headers(Role.PLATFORM_ADMIN, is_admin=True)
    cid = uuid.uuid4()

    clinic = Clinic(
        id=cid,
        name="Clinic Active",
        slug="clinic-active",
        status="trial",
        time_zone="Asia/Karachi",
        created_at=datetime.now(UTC),
    )

    # 1. Valid status transition: trial -> active
    mock_get = MagicMock()
    mock_get.scalar_one_or_none.return_value = clinic
    admin_mock_db.execute.return_value = mock_get

    res = client.patch(
        f"/api/v1/admin/clinics/{cid}/status",
        headers=admin_headers,
        json={"status": "active", "reason": "Completed onboarding walkthrough"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "active"

    # 2. Invalid status transition: active -> trial (not allowed)
    res_inv = client.patch(
        f"/api/v1/admin/clinics/{cid}/status",
        headers=admin_headers,
        json={"status": "trial", "reason": "Attempting invalid downgrade"},
    )
    assert res_inv.status_code == 400
    assert res_inv.json()["code"] == "INVALID_STATUS_TRANSITION"
