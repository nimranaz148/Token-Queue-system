import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import ValidationError

from app.integrations.realtime import (
    RealtimePublishError,
    RealtimeQueuePayload,
    RealtimeRateLimitError,
    RealtimeTimeoutError,
    SupabaseRealtimeClient,
)


@pytest.mark.asyncio
async def test_realtime_broadcast_happy_path() -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    mock_response = httpx.Response(
        status_code=200,
        json={"status": "ok"},
        request=httpx.Request("POST", "https://api.supabase.com/realtime/v1/api/broadcast"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        client = SupabaseRealtimeClient(
            base_url="https://api.supabase.com",
            service_role_key="service-key-test",
        )

        result = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="token.created",
            token_number=18,
            current_token=12,
            total_waiting=5,
            estimated_wait_minutes=50,
        )

        assert result["status"] == "published"
        assert result["topic"] == f"queue:{clinic_id}:{doctor_id}"
        assert result["event"] == "token.created"
        assert result["payload"]["token_number"] == 18
        assert result["payload"]["current_token"] == 12
        assert result["payload"]["total_waiting"] == 5

        # Verify network request call
        assert mock_post.called
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["headers"]["apikey"] == "service-key-test"
        assert call_kwargs["headers"]["Authorization"] == "Bearer service-key-test"
        assert call_kwargs["json"]["messages"][0]["topic"] == f"queue:{clinic_id}:{doctor_id}"


@pytest.mark.asyncio
async def test_realtime_broadcast_timeout_handling() -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    with patch(
        "httpx.AsyncClient.post",
        side_effect=httpx.TimeoutException("Connection timed out"),
    ):
        client = SupabaseRealtimeClient(
            base_url="https://api.supabase.com",
            service_role_key="service-key-test",
        )

        # Default non-blocking mode: logs warning and returns fallback status
        result = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="queue.update",
            total_waiting=3,
            non_blocking=True,
        )
        assert result["status"] == "timeout_fallback_to_polling"

        # Blocking mode: raises RealtimeTimeoutError
        with pytest.raises(RealtimeTimeoutError):
            await client.broadcast_queue_update(
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                event="queue.update",
                total_waiting=3,
                non_blocking=False,
            )


@pytest.mark.asyncio
async def test_realtime_broadcast_error_response_handling() -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    # 1. 500 Server error
    mock_500 = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("POST", "https://api.supabase.com/realtime/v1/api/broadcast"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_500
        client = SupabaseRealtimeClient()

        # Non-blocking
        res = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="token.called",
            non_blocking=True,
        )
        assert res["status"] == "error"
        assert res["status_code"] == 500

        # Blocking
        with pytest.raises(RealtimePublishError) as exc_info:
            await client.broadcast_queue_update(
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                event="token.called",
                non_blocking=False,
            )
        assert exc_info.value.status_code == 500

    # 2. 429 Rate limit
    mock_429 = httpx.Response(
        status_code=429,
        text="Too Many Requests",
        request=httpx.Request("POST", "https://api.supabase.com/realtime/v1/api/broadcast"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_429
        client = SupabaseRealtimeClient()

        # Non-blocking
        res = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="token.called",
            non_blocking=True,
        )
        assert res["status"] == "rate_limited"

        # Blocking
        with pytest.raises(RealtimeRateLimitError):
            await client.broadcast_queue_update(
                clinic_id=clinic_id,
                doctor_id=doctor_id,
                event="token.called",
                non_blocking=False,
            )


@pytest.mark.asyncio
async def test_realtime_broadcast_duplicate_suppression() -> None:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    idempotency_key = "idemp-broadcast-test-123"

    mock_200 = httpx.Response(
        status_code=200,
        json={"status": "ok"},
        request=httpx.Request("POST", "https://api.supabase.com/realtime/v1/api/broadcast"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_200
        client = SupabaseRealtimeClient()

        # First delivery succeeds
        first = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="token.created",
            token_number=21,
            idempotency_key=idempotency_key,
        )
        assert first["status"] == "published"
        assert mock_post.call_count == 1

        # Second delivery with same idempotency key is suppressed
        second = await client.broadcast_queue_update(
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            event="token.created",
            token_number=21,
            idempotency_key=idempotency_key,
        )
        assert second["status"] == "duplicate_suppressed"
        # Network post must not be called a second time
        assert mock_post.call_count == 1


def test_rule_10_pii_strictly_forbidden() -> None:
    """Non-negotiable architectural invariant: Rule 10.

    Realtime payloads carry token numbers and counts only.
    No patient name or phone ever goes into a broadcast.
    """
    # Valid payload
    payload = RealtimeQueuePayload(
        token_number=15,
        current_token=10,
        total_waiting=4,
        estimated_wait_minutes=40,
        event="token.created",
        timestamp="2026-11-02T00:00:00Z",
    )
    assert payload.token_number == 15

    # Violations: Patient name forbidden
    with pytest.raises(ValidationError) as exc:
        RealtimeQueuePayload.model_validate(
            {
                "token_number": 15,
                "event": "token.created",
                "timestamp": "2026-11-02T00:00:00Z",
                "patient_name": "Muhammad Ali",
            }
        )
    assert "Rule 10 violation" in str(exc.value)

    # Violations: Phone number forbidden
    with pytest.raises(ValidationError) as exc:
        RealtimeQueuePayload.model_validate(
            {
                "token_number": 15,
                "event": "token.created",
                "timestamp": "2026-11-02T00:00:00Z",
                "phone": "+923001234567",
            }
        )
    assert "Rule 10 violation" in str(exc.value)

    # Violations: Notes forbidden
    with pytest.raises(ValidationError) as exc:
        RealtimeQueuePayload.model_validate(
            {
                "token_number": 15,
                "event": "token.created",
                "timestamp": "2026-11-02T00:00:00Z",
                "notes": "Patient has severe fever",
            }
        )
    assert "Rule 10 violation" in str(exc.value)
