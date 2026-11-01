import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.doctor import Doctor
from app.models.member import ClinicMember
from app.schemas.audit import AuditAction
from app.schemas.auth import Role

client = TestClient(app)


def make_auth_headers(role: str, clinic_id: uuid.UUID | None = None) -> dict[str, str]:
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "email": f"{role}@example.com",
            "role": role,
            "clinic_id": str(clinic_id) if clinic_id else None,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_db() -> Generator[AsyncMock, None, None]:
    session = AsyncMock()
    session.add = MagicMock()

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield session
    app.dependency_overrides.pop(get_db, None)


def test_list_members_requires_owner(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()

    # 1. Unauthenticated -> 401
    res = client.get("/api/v1/members")
    assert res.status_code == 401

    # 2. Doctor -> 403
    doc_headers = make_auth_headers(Role.DOCTOR, clinic_id=clinic_id)
    res_doc = client.get("/api/v1/members", headers=doc_headers)
    assert res_doc.status_code == 403

    # 3. Reception -> 403
    rec_headers = make_auth_headers(Role.RECEPTION, clinic_id=clinic_id)
    res_rec = client.get("/api/v1/members", headers=rec_headers)
    assert res_rec.status_code == 403

    # 4. Owner without clinic context -> 403
    owner_no_clinic = make_auth_headers(Role.OWNER, clinic_id=None)
    res_no_clinic = client.get("/api/v1/members", headers=owner_no_clinic)
    assert res_no_clinic.status_code == 403


def test_list_members_success(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    now = datetime.now(UTC)
    member1 = ClinicMember(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        user_id=uuid.uuid4(),
        name="Owner Tariq",
        email="owner@example.com",
        phone="+923001234567",
        role="owner",
        doctor_id=None,
        active=True,
        created_at=now,
        updated_at=now,
    )
    member2 = ClinicMember(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        user_id=uuid.uuid4(),
        name="Dr. Imran",
        email="imran@example.com",
        phone="+923007654321",
        role="doctor",
        doctor_id=uuid.uuid4(),
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_exec = MagicMock()
    mock_exec.all.return_value = [
        (member1, None),
        (member2, "Dr. Imran Khan"),
    ]
    mock_db.execute.return_value = mock_exec

    res = client.get("/api/v1/members", headers=owner_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["name"] == "Owner Tariq"
    assert data["items"][0]["role"] == "owner"
    assert data["items"][1]["name"] == "Dr. Imran"
    assert data["items"][1]["doctor_name"] == "Dr. Imran Khan"


def test_invite_member_success(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    # Email check returns None (no duplicate)
    mock_email_check = MagicMock()
    mock_email_check.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_email_check

    payload = {
        "name": "Sarah Receptionist",
        "email": "sarah@clinic.com",
        "phone": "+923001112233",
        "role": "reception",
    }

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        res = client.post("/api/v1/members", headers=owner_headers, json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Sarah Receptionist"
        assert data["email"] == "sarah@clinic.com"
        assert data["role"] == "reception"
        assert data["active"] is True

        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[1]
        assert audit_call["action"] == AuditAction.MEMBER_INVITE
        assert audit_call["clinic_id"] == clinic_id
        assert audit_call["after"]["name"] == "Sarah Receptionist"


def test_invite_member_duplicate_email(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    existing = ClinicMember(
        id=uuid.uuid4(),
        clinic_id=clinic_id,
        user_id=uuid.uuid4(),
        name="Existing",
        email="existing@clinic.com",
        role="reception",
    )
    mock_email_check = MagicMock()
    mock_email_check.scalar_one_or_none.return_value = existing
    mock_db.execute.return_value = mock_email_check

    payload = {
        "name": "Duplicate Sarah",
        "email": "existing@clinic.com",
        "role": "reception",
    }
    res = client.post("/api/v1/members", headers=owner_headers, json=payload)
    assert res.status_code == 409
    assert res.json()["code"] == "EMAIL_ALREADY_MEMBER"


def test_invite_doctor_requires_doctor_id(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    mock_email_check = MagicMock()
    mock_email_check.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_email_check

    payload = {
        "name": "Dr. No Link",
        "email": "doc@clinic.com",
        "role": "doctor",
        "doctor_id": None,
    }
    res = client.post("/api/v1/members", headers=owner_headers, json=payload)
    assert res.status_code == 422
    assert res.json()["code"] == "DOCTOR_ID_REQUIRED"


def test_invite_doctor_success_with_link(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    # 1st execute: email check -> None
    mock_email_check = MagicMock()
    mock_email_check.scalar_one_or_none.return_value = None

    # 2nd execute: doctor check -> Doctor
    doc = Doctor(
        id=doctor_id,
        clinic_id=clinic_id,
        name="Dr. Zafar",
        specialty="Cardiology",
        active=True,
    )
    mock_doc_check = MagicMock()
    mock_doc_check.scalar_one_or_none.return_value = doc

    mock_db.execute.side_effect = [mock_email_check, mock_doc_check]

    payload = {
        "name": "Dr. Zafar Iqbal",
        "email": "zafar@clinic.com",
        "role": "doctor",
        "doctor_id": str(doctor_id),
    }

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        res = client.post("/api/v1/members", headers=owner_headers, json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["role"] == "doctor"
        assert data["doctor_id"] == str(doctor_id)
        assert data["doctor_name"] == "Dr. Zafar"

        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[1]
        assert audit_call["action"] == AuditAction.MEMBER_INVITE


def test_update_member_role_and_audit(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    member_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    now = datetime.now(UTC)
    member = ClinicMember(
        id=member_id,
        clinic_id=clinic_id,
        user_id=uuid.uuid4(),
        name="Staff User",
        email="user@clinic.com",
        role="reception",
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_member_res = MagicMock()
    mock_member_res.scalar_one_or_none.return_value = member
    mock_db.execute.return_value = mock_member_res

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        res = client.patch(
            f"/api/v1/members/{member_id}",
            headers=owner_headers,
            json={"role": "owner"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "owner"

        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[1]
        assert audit_call["action"] == AuditAction.MEMBER_ROLE_CHANGE
        assert audit_call["before"]["role"] == "reception"
        assert audit_call["after"]["role"] == "owner"


def test_deactivate_member_and_audit(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    member_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    now = datetime.now(UTC)
    member = ClinicMember(
        id=member_id,
        clinic_id=clinic_id,
        user_id=uuid.uuid4(),
        name="Staff User",
        email="user@clinic.com",
        role="reception",
        active=True,
        created_at=now,
        updated_at=now,
    )

    mock_member_res = MagicMock()
    mock_member_res.scalar_one_or_none.return_value = member
    mock_db.execute.return_value = mock_member_res

    with patch("app.services.audit.AuditService.record_audit") as mock_audit:
        res = client.patch(
            f"/api/v1/members/{member_id}",
            headers=owner_headers,
            json={"active": False},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["active"] is False

        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[1]
        assert audit_call["action"] == AuditAction.MEMBER_DEACTIVATE
        assert audit_call["after"]["active"] is False


def test_update_member_not_found(mock_db: AsyncMock) -> None:
    clinic_id = uuid.uuid4()
    member_id = uuid.uuid4()
    owner_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_id)

    mock_member_res = MagicMock()
    mock_member_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_member_res

    res = client.patch(
        f"/api/v1/members/{member_id}",
        headers=owner_headers,
        json={"name": "New Name"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "MEMBER_NOT_FOUND"


def test_cross_clinic_member_access_returns_404(mock_db: AsyncMock) -> None:
    clinic_a = uuid.uuid4()
    member_b_id = uuid.uuid4()
    owner_a_headers = make_auth_headers(Role.OWNER, clinic_id=clinic_a)

    # In tenant isolation under clinic_a, member belonging to clinic_b returns None
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res

    res = client.patch(
        f"/api/v1/members/{member_b_id}",
        headers=owner_a_headers,
        json={"name": "Attacker Update"},
    )
    assert res.status_code == 404
    assert res.json()["code"] == "MEMBER_NOT_FOUND"
