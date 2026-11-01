import time
from unittest.mock import AsyncMock

import httpx
import pytest

from app.integrations.vendor_auth import (
    VendorAuthError,
    VendorToken,
    VendorTokenManager,
    VendorTokenRevokedError,
)


@pytest.fixture
def mock_http_client() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.mark.asyncio
async def test_expired_token_refreshes_without_user_action(
    mock_http_client: AsyncMock,
) -> None:
    """Acceptance criterion 1 for Task 46:

    Expired token refreshes without user action.
    """
    initial_expired_token = VendorToken(
        access_token="old-expired-access-token",
        refresh_token="valid-refresh-token",
        expires_at=time.time() - 300,  # Expired 5 minutes ago
    )

    # Mock vendor token endpoint response
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "fresh-access-token-12345",
        "refresh_token": "fresh-refresh-token-67890",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_http_client.post.return_value = mock_response

    manager = VendorTokenManager(
        provider="supabase",
        token_endpoint="https://api.supabase.com/v1/oauth/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        reconsent_path="/settings/integrations/supabase/reconnect",
        initial_token=initial_expired_token,
        http_client=mock_http_client,
    )

    # Proactively fetch access token - should trigger automatic refresh
    access_token = await manager.get_valid_access_token()

    # 1. Assert new token returned without user intervention
    assert access_token == "fresh-access-token-12345"

    # 2. Assert HTTP refresh call was made with refresh_token grant
    assert mock_http_client.post.called
    call_args = mock_http_client.post.call_args
    data_sent = call_args.kwargs["data"]
    assert data_sent["grant_type"] == "refresh_token"
    assert data_sent["refresh_token"] == "valid-refresh-token"

    # 3. Assert internal token state was updated
    current_token = manager.get_current_token()
    assert current_token is not None
    assert current_token.access_token == "fresh-access-token-12345"
    assert current_token.refresh_token == "fresh-refresh-token-67890"
    assert current_token.is_expired is False


@pytest.mark.asyncio
async def test_non_expired_token_returns_directly_without_refresh(
    mock_http_client: AsyncMock,
) -> None:
    """Active tokens are returned immediately without contacting the vendor."""
    valid_token = VendorToken(
        access_token="still-valid-access-token",
        refresh_token="valid-refresh-token",
        expires_at=time.time() + 1800,  # Valid for 30 more minutes
    )

    manager = VendorTokenManager(
        provider="supabase",
        token_endpoint="https://api.supabase.com/v1/oauth/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        initial_token=valid_token,
        http_client=mock_http_client,
    )

    token = await manager.get_valid_access_token()
    assert token == "still-valid-access-token"
    assert not mock_http_client.post.called


@pytest.mark.asyncio
async def test_revoked_token_produces_clear_reconsent_path(
    mock_http_client: AsyncMock,
) -> None:
    """Acceptance criterion 2 for Task 46:

    Revoked token produces a clear re-consent path.
    """
    expired_token = VendorToken(
        access_token="expired-token",
        refresh_token="revoked-refresh-token",
        expires_at=time.time() - 60,
    )

    # Vendor returns RFC 6749 invalid_grant indicating token was revoked
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": "invalid_grant",
        "error_description": "Token has been revoked by the resource owner",
    }
    mock_response.text = '{"error": "invalid_grant"}'
    mock_http_client.post.return_value = mock_response

    expected_reconsent_url = "/settings/integrations/supabase/reconnect"
    manager = VendorTokenManager(
        provider="supabase",
        token_endpoint="https://api.supabase.com/v1/oauth/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        reconsent_path=expected_reconsent_url,
        initial_token=expired_token,
        http_client=mock_http_client,
    )

    with pytest.raises(VendorTokenRevokedError) as exc_info:
        await manager.get_valid_access_token()

    # Assert clear re-consent path and message
    assert exc_info.value.reconsent_url == expected_reconsent_url
    assert exc_info.value.provider == "supabase"
    assert "revoked" in exc_info.value.message.lower()
    assert "re-authenticate" in exc_info.value.message.lower()

    # Stored token must be cleared to prevent repeated failure loops
    assert manager.get_current_token() is None


@pytest.mark.asyncio
async def test_vendor_server_error_raises_vendor_auth_error(
    mock_http_client: AsyncMock,
) -> None:
    """Server error (500) from vendor raises VendorAuthError."""
    expired_token = VendorToken(
        access_token="expired-token",
        refresh_token="refresh-token",
        expires_at=time.time() - 60,
    )

    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.status_code = 503
    mock_response.text = "Service Temporarily Unavailable"
    mock_response.json.side_effect = ValueError("Not JSON")
    mock_http_client.post.return_value = mock_response

    manager = VendorTokenManager(
        provider="supabase",
        token_endpoint="https://api.supabase.com/v1/oauth/token",
        client_id="test-client-id",
        client_secret="test-client-secret",
        initial_token=expired_token,
        http_client=mock_http_client,
    )

    with pytest.raises(VendorAuthError) as exc_info:
        await manager.get_valid_access_token()

    assert "HTTP 503" in exc_info.value.message
