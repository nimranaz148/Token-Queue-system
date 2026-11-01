from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.supabase_auth import (
    SupabaseAuthClient,
    SupabaseAuthError,
    SupabaseAuthRateLimitError,
    SupabaseAuthTimeoutError,
)


@pytest.fixture
def auth_client() -> SupabaseAuthClient:
    return SupabaseAuthClient(
        base_url="https://mock-supabase.test",
        service_role_key="test-service-key",
        jwt_secret="test-secret-key-at-least-32-chars-long",
        timeout_seconds=2.0,
    )


@pytest.mark.asyncio
async def test_supabase_auth_happy_path(auth_client: SupabaseAuthClient) -> None:
    """Contract test against sandbox response for magic link delivery."""
    mock_response = httpx.Response(
        status_code=200,
        json={"message": "Magic link sent"},
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "https://mock-supabase.test/auth/v1/magiclink"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = await auth_client.send_magic_link(
            email="doctor@example.com",
            redirect_to="https://app.clinic.com/dashboard",
        )

        assert res["message"] == "Magic link sent"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["email"] == "doctor@example.com"
        assert (
            call_kwargs["json"]["options"]["email_redirect_to"]
            == "https://app.clinic.com/dashboard"
        )
        assert call_kwargs["headers"]["apikey"] == "test-service-key"
        assert "Bearer test-service-key" in call_kwargs["headers"]["Authorization"]


@pytest.mark.asyncio
async def test_supabase_auth_timeout_handling(auth_client: SupabaseAuthClient) -> None:
    """Timeout test ensuring retry eligibility is raised."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(SupabaseAuthTimeoutError) as exc_info:
            await auth_client.send_magic_link(email="staff@example.com")

        assert exc_info.value.status_code == 504
        assert exc_info.value.error_code == "AUTH_TIMEOUT"


@pytest.mark.asyncio
async def test_supabase_auth_error_response_handling(auth_client: SupabaseAuthClient) -> None:
    """Error response tests for 400 Bad Request and 429 Rate Limit."""
    # 1. Test 400 Bad Request
    mock_400 = httpx.Response(
        status_code=400,
        json={"msg": "Invalid email address format"},
        headers={"content-type": "application/json"},
        request=httpx.Request("POST", "https://mock-supabase.test/auth/v1/magiclink"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_400

        with pytest.raises(SupabaseAuthError) as exc_info:
            await auth_client.send_magic_link(email="invalid-email")

        assert exc_info.value.status_code == 400
        assert "Invalid email address" in exc_info.value.message

    # 2. Test 429 Rate Limit
    mock_429 = httpx.Response(
        status_code=429,
        text="Rate limit exceeded. Too many requests.",
        request=httpx.Request("POST", "https://mock-supabase.test/auth/v1/magiclink"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_429

        with pytest.raises(SupabaseAuthRateLimitError) as exc_info:
            await auth_client.send_magic_link(email="busy@example.com")

        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_supabase_auth_duplicate_delivery_suppressed(auth_client: SupabaseAuthClient) -> None:
    """Duplicate delivery with idempotency key is suppressed within TTL."""
    mock_response = httpx.Response(
        status_code=200,
        json={"message": "Sent"},
        request=httpx.Request("POST", "https://mock-supabase.test/auth/v1/magiclink"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # First request succeeds
        res1 = await auth_client.send_magic_link(
            email="user@example.com",
            idempotency_key="idemp-key-12345",
        )
        assert res1["message"] == "Sent"
        assert mock_post.call_count == 1

        # Duplicate delivery with same key is suppressed without sending extra HTTP call
        res2 = await auth_client.send_magic_link(
            email="user@example.com",
            idempotency_key="idemp-key-12345",
        )
        assert res2["status"] == "duplicate_suppressed"
        # Call count remains 1
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_supabase_jwks_caching_10min(auth_client: SupabaseAuthClient) -> None:
    """PRD §13.3 requirement: JWKS cached 10 minutes."""
    jwks_data = {"keys": [{"kid": "key-1", "kty": "RSA"}]}
    mock_jwks = httpx.Response(
        status_code=200,
        json=jwks_data,
        request=httpx.Request("GET", "https://mock-supabase.test/auth/v1/.well-known/jwks.json"),
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_jwks

        # First fetch calls network
        keys1 = await auth_client.get_jwks()
        assert keys1 == jwks_data
        assert mock_get.call_count == 1

        # Second fetch returns cached result without network request
        keys2 = await auth_client.get_jwks()
        assert keys2 == jwks_data
        assert mock_get.call_count == 1

        # Force refresh fetches again
        keys3 = await auth_client.get_jwks(force_refresh=True)
        assert keys3 == jwks_data
        assert mock_get.call_count == 2
