import uuid
from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.errors import AppException
from app.core.security import create_access_token, decode_token
from app.main import app
from app.schemas.auth import Role


async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)
    yield mock_session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_create_and_decode_valid_token() -> None:
    user_id = str(uuid.uuid4())
    data = {
        "sub": user_id,
        "email": "doctor@example.com",
        "role": Role.DOCTOR,
    }
    token = create_access_token(data)
    decoded = decode_token(token)
    assert decoded["sub"] == user_id
    assert decoded["email"] == "doctor@example.com"
    assert decoded["role"] == Role.DOCTOR
    assert decoded["type"] == "access"


def test_expired_token_raises_exception() -> None:
    data = {"sub": str(uuid.uuid4()), "role": Role.DOCTOR}
    token = create_access_token(data, expires_delta=timedelta(seconds=-10))
    with pytest.raises(AppException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "TOKEN_EXPIRED"


def test_invalid_signature_raises_exception() -> None:
    with pytest.raises(AppException) as exc_info:
        decode_token("not.a.valid.jwt.token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_TOKEN"


def test_login_success() -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@example.com"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_login_invalid_user() -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com"},
    )
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "INVALID_CREDENTIALS"
    assert data["status"] == 400


def test_refresh_token_success() -> None:
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@example.com"},
    )
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_with_access_token_fails() -> None:
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@example.com"},
    )
    access_token = login_res.json()["access_token"]

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert refresh_res.status_code == 401
    assert refresh_res.json()["code"] == "INVALID_TOKEN"


def test_me_endpoint_requires_auth() -> None:
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_me_endpoint_with_valid_token() -> None:
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "reception@example.com"},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "reception@example.com"
    assert data["role"] == Role.RECEPTION


# Role Permission Matrix Tests (PRD §14.2)


def get_token_for(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email})
    return str(res.json()["access_token"])


def test_platform_admin_permissions() -> None:
    admin_token = get_token_for("admin@example.com")
    doctor_token = get_token_for("doctor@example.com")

    # Platform admin can access admin endpoint
    res_admin = client.get(
        "/api/v1/auth/test/platform-admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200

    # Doctor cannot access platform admin endpoint
    res_forbidden = client.get(
        "/api/v1/auth/test/platform-admin",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["code"] == "FORBIDDEN"


def test_owner_permissions() -> None:
    owner_token = get_token_for("owner@example.com")
    reception_token = get_token_for("reception@example.com")

    # Owner can access owner endpoint
    res_owner = client.get(
        "/api/v1/auth/test/owner",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert res_owner.status_code == 200

    # Owner can also access doctor and reception endpoints
    assert (
        client.get(
            "/api/v1/auth/test/doctor",
            headers={"Authorization": f"Bearer {owner_token}"},
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/auth/test/reception",
            headers={"Authorization": f"Bearer {owner_token}"},
        ).status_code
        == 200
    )

    # Reception cannot access owner endpoint
    res_forbidden = client.get(
        "/api/v1/auth/test/owner",
        headers={"Authorization": f"Bearer {reception_token}"},
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["code"] == "FORBIDDEN"


def test_doctor_permissions() -> None:
    doctor_token = get_token_for("doctor@example.com")
    reception_token = get_token_for("reception@example.com")

    # Doctor can access doctor endpoint
    res_doc = client.get(
        "/api/v1/auth/test/doctor",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_doc.status_code == 200

    # Doctor cannot access reception endpoint
    res_forbidden = client.get(
        "/api/v1/auth/test/reception",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert res_forbidden.status_code == 403

    # Reception cannot access doctor endpoint
    res_doc_forbidden = client.get(
        "/api/v1/auth/test/doctor",
        headers={"Authorization": f"Bearer {reception_token}"},
    )
    assert res_doc_forbidden.status_code == 403
