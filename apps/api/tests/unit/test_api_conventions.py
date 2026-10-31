from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_versioned_prefix_conventions() -> None:
    """All domain endpoints must be versioned under /api/v1 prefix."""
    openapi_spec = app.openapi()
    paths = openapi_spec.get("paths", {})

    for path in paths:
        if path == "/":
            continue  # Root health/ping route
        assert path.startswith("/api/v1/"), f"Path {path} does not start with /api/v1/"


def test_rfc7807_error_format_on_unauthorized() -> None:
    """Authentication failure must return RFC 7807 Problem Details."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    data: dict[str, Any] = res.json()

    assert data.get("type") == "about:blank"
    assert data.get("title") == "Unauthorized"
    assert data.get("status") == 401
    assert "detail" in data
    assert data.get("code") == "UNAUTHORIZED"


def test_rfc7807_error_format_on_forbidden() -> None:
    """Authorization failure must return RFC 7807 Problem Details."""
    # Obtain token for doctor
    login_res = client.post("/api/v1/auth/login", json={"email": "doctor@example.com"})
    token = login_res.json()["access_token"]

    # Try to access owner-only endpoint
    res = client.get(
        "/api/v1/auth/test/owner",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    data: dict[str, Any] = res.json()

    assert data.get("type") == "about:blank"
    assert data.get("title") == "Forbidden"
    assert data.get("status") == 403
    assert "detail" in data
    assert data.get("code") == "FORBIDDEN"


def test_rfc7807_error_format_on_bad_request() -> None:
    """Invalid credentials must return RFC 7807 Problem Details with 400."""
    res = client.post("/api/v1/auth/login", json={"email": "nonexistent@example.com"})
    assert res.status_code == 400
    data: dict[str, Any] = res.json()

    assert data.get("type") == "about:blank"
    assert data.get("title") == "Bad Request"
    assert data.get("status") == 400
    assert "detail" in data
    assert data.get("code") == "INVALID_CREDENTIALS"
