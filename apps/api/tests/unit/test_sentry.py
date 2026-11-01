from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.sentry import SentryClient


@pytest.fixture
def sentry_client() -> SentryClient:
    return SentryClient(
        dsn="https://publickey123@o12345.ingest.sentry.io/987654",
        environment="test",
        timeout_seconds=2.0,
    )


@pytest.mark.asyncio
async def test_sentry_happy_path(sentry_client: SentryClient) -> None:
    """Contract test against sandbox Sentry store API response."""
    mock_response = httpx.Response(
        status_code=200,
        json={"id": "mock-event-id-987"},
        request=httpx.Request("POST", "https://o12345.ingest.sentry.io/api/987654/store/"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = await sentry_client.capture_exception(
            exc=ValueError("Database query failed"),
            tags={"clinic_id": "test-clinic-1"},
            extra={"action": "test_query"},
        )

        assert res["status"] == "delivered"
        assert "event_id" in res
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert "X-Sentry-Auth" in call_kwargs["headers"]
        assert "sentry_key=publickey123" in call_kwargs["headers"]["X-Sentry-Auth"]
        assert call_kwargs["json"]["level"] == "error"
        assert call_kwargs["json"]["tags"]["clinic_id"] == "test-clinic-1"


@pytest.mark.asyncio
async def test_sentry_timeout_non_blocking_buffer(sentry_client: SentryClient) -> None:
    """Timeout test ensuring non-blocking execution and local buffering."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Sentry API timed out")

        # Capture exception should not raise or block
        res = await sentry_client.capture_exception(exc=RuntimeError("Timeout trigger"))

        assert res["status"] == "timeout_buffered"
        assert len(sentry_client._local_buffer) == 1
        assert sentry_client._local_buffer[0]["message"] == "Timeout trigger"


@pytest.mark.asyncio
async def test_sentry_error_response_handling(sentry_client: SentryClient) -> None:
    """Error responses (e.g. 429 quota, 401 bad DSN) buffer locally without bubbling."""
    # 1. Test 429 rate limit
    mock_429 = httpx.Response(
        status_code=429,
        text="Daily event quota exceeded",
        request=httpx.Request("POST", "https://o12345.ingest.sentry.io/api/987654/store/"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_429
        res = await sentry_client.capture_message("Informational warning", level="warning")

        assert res["status"] == "rate_limited_buffered"
        assert len(sentry_client._local_buffer) == 1

    # 2. Test 401 unauthorized
    mock_401 = httpx.Response(
        status_code=401,
        text="Invalid DSN public key",
        request=httpx.Request("POST", "https://o12345.ingest.sentry.io/api/987654/store/"),
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_401
        res2 = await sentry_client.capture_exception(exc=KeyError("Missing key"))

        assert res2["status"] == "error_buffered"
        assert res2["status_code"] == 401


@pytest.mark.asyncio
async def test_sentry_duplicate_delivery_suppression(sentry_client: SentryClient) -> None:
    """Duplicate events sharing an idempotency key are suppressed."""
    mock_response = httpx.Response(
        status_code=200,
        json={"id": "evt-1"},
        request=httpx.Request("POST", "https://o12345.ingest.sentry.io/api/987654/store/"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        # First delivery
        res1 = await sentry_client.capture_message(
            "Service restarted",
            idempotency_key="restart-event-99",
        )
        assert res1["status"] == "delivered"
        assert mock_post.call_count == 1

        # Duplicate delivery with same key
        res2 = await sentry_client.capture_message(
            "Service restarted",
            idempotency_key="restart-event-99",
        )
        assert res2["status"] == "duplicate_suppressed"
        # Network call should not happen again
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_sentry_pii_masking_enforcement(sentry_client: SentryClient) -> None:
    """Verify sensitive PII fields (phone, email, password) are masked in extra."""
    mock_response = httpx.Response(
        status_code=200,
        json={"id": "pii-masked-1"},
        request=httpx.Request("POST", "https://o12345.ingest.sentry.io/api/987654/store/"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        await sentry_client.capture_exception(
            exc=ValueError("Failed processing patient"),
            extra={
                "phone": "+923001234567",
                "email": "patient@example.com",
                "password": "supersecretpassword",
                "non_sensitive_id": "item-99",
            },
        )

        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        extra = payload["extra"]
        # Sensitive fields must be masked by mask_sensitive_data
        assert extra["phone"] != "+923001234567"
        assert extra["password"] == "[REDACTED]"
        assert extra["non_sensitive_id"] == "item-99"
