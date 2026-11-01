from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.errors import AppException
from app.integrations.sandbox import (
    CLOUDFLARE_TURNSTILE_VERIFY_URL,
)
from app.integrations.turnstile import (
    TURNSTILE_TEST_FAIL_TOKEN,
    TurnstileService,
)


@pytest.fixture(autouse=True)
def reset_used_tokens() -> None:
    TurnstileService._used_tokens.clear()


@pytest.mark.asyncio
async def test_turnstile_verify_happy_path() -> None:
    """Contract test proving happy path against recorded Cloudflare siteverify response."""
    token = "valid-cf-turnstile-token-sample-123"
    mock_200 = httpx.Response(
        status_code=200,
        json={
            "success": True,
            "challenge_ts": "2026-11-02T01:00:00.000Z",
            "hostname": "shifa.clinic.pk",
            "error-codes": [],
            "action": "book_token",
            "cdata": "session-xyz",
        },
        request=httpx.Request("POST", CLOUDFLARE_TURNSTILE_VERIFY_URL),
    )

    with patch.dict("os.environ", {"CLOUDFLARE_TURNSTILE_SECRET_KEY": "prod-secret-key-123"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_200

            result = await TurnstileService.verify_token(token=token, client_ip="192.168.1.100")
            assert result is True

            # Assert correct form payload sent
            assert mock_post.called
            data_sent = mock_post.call_args.kwargs["data"]
            assert data_sent["secret"] == "prod-secret-key-123"
            assert data_sent["response"] == token
            assert data_sent["remoteip"] == "192.168.1.100"


@pytest.mark.asyncio
async def test_turnstile_verify_timeout_handling() -> None:
    """Proves timeout is handled gracefully with clear client error code."""
    token = "timeout-token-sample-456"

    with patch.dict("os.environ", {"CLOUDFLARE_TURNSTILE_SECRET_KEY": "prod-secret-key-123"}):
        with patch(
            "httpx.AsyncClient.post",
            side_effect=httpx.TimeoutException("Turnstile connection timed out"),
        ):
            with pytest.raises(AppException) as exc_info:
                await TurnstileService.verify_token(token=token)

            assert exc_info.value.code == "TURNSTILE_TIMEOUT"
            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_turnstile_verify_upstream_error_response() -> None:
    """Proves 5xx upstream failure and 4xx challenge rejections are handled."""
    token = "error-token-sample-789"

    with patch.dict("os.environ", {"CLOUDFLARE_TURNSTILE_SECRET_KEY": "prod-secret-key-123"}):
        # 1. 500 Bad Gateway from Cloudflare
        mock_502 = httpx.Response(
            status_code=502,
            text="Bad Gateway",
            request=httpx.Request("POST", CLOUDFLARE_TURNSTILE_VERIFY_URL),
        )
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_502
            with pytest.raises(AppException) as exc_info:
                await TurnstileService.verify_token(token=token)
            assert exc_info.value.code == "TURNSTILE_SERVICE_ERROR"

        # 2. Rejection response (invalid challenge solution)
        token_rejected = "rejected-challenge-token-000"
        mock_rejected = httpx.Response(
            status_code=200,
            json={
                "success": False,
                "error-codes": ["invalid-input-response"],
            },
            request=httpx.Request("POST", CLOUDFLARE_TURNSTILE_VERIFY_URL),
        )
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_rejected
            with pytest.raises(AppException) as exc_info:
                await TurnstileService.verify_token(token=token_rejected)
            assert exc_info.value.code == "TURNSTILE_FAILED"


@pytest.mark.asyncio
async def test_turnstile_verify_duplicate_delivery() -> None:
    """Proves duplicate delivery of the same Turnstile token is caught and rejected."""
    token = "single-use-token-abc-999"

    mock_200 = httpx.Response(
        status_code=200,
        json={"success": True},
        request=httpx.Request("POST", CLOUDFLARE_TURNSTILE_VERIFY_URL),
    )

    with patch.dict("os.environ", {"CLOUDFLARE_TURNSTILE_SECRET_KEY": "prod-secret-key-123"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_200

            # First delivery succeeds
            first = await TurnstileService.verify_token(token=token)
            assert first is True

            # Duplicate delivery with identical token is rejected before network hit
            with pytest.raises(AppException) as exc_info:
                await TurnstileService.verify_token(token=token)
            assert exc_info.value.code == "TURNSTILE_DUPLICATE_TOKEN"

            # Upstream Cloudflare timeout-or-duplicate response
            mock_cf_duplicate = httpx.Response(
                status_code=200,
                json={
                    "success": False,
                    "error-codes": ["timeout-or-duplicate"],
                },
                request=httpx.Request("POST", CLOUDFLARE_TURNSTILE_VERIFY_URL),
            )
            mock_post.return_value = mock_cf_duplicate
            with pytest.raises(AppException) as exc_info_cf:
                await TurnstileService.verify_token(token="another-fresh-token")
            assert exc_info_cf.value.code == "TURNSTILE_DUPLICATE_TOKEN"


@pytest.mark.asyncio
async def test_turnstile_empty_and_fail_token() -> None:
    """Tests empty token and explicit fail token."""
    with pytest.raises(AppException) as exc_empty:
        await TurnstileService.verify_token(token="")
    assert exc_empty.value.code == "TURNSTILE_FAILED"

    with pytest.raises(AppException) as exc_fail:
        await TurnstileService.verify_token(token=TURNSTILE_TEST_FAIL_TOKEN)
    assert exc_fail.value.code == "TURNSTILE_FAILED"
