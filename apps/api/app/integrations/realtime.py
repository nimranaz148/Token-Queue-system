import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings

logger = logging.getLogger(__name__)

FORBIDDEN_PII_FIELDS = {
    "patient_name",
    "name",
    "patient_phone",
    "phone",
    "phone_number",
    "notes",
    "medical_notes",
    "medicines_advice",
    "diagnosis",
    "cnic",
}


class RealtimePublishError(Exception):
    """Base exception for Supabase Realtime broadcast failures (PRD §13.3 I-002)."""

    def __init__(
        self, message: str, status_code: int = 500, error_code: str = "REALTIME_ERROR"
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class RealtimeTimeoutError(RealtimePublishError):
    """Raised when Supabase Realtime HTTP request times out."""

    def __init__(self, message: str = "Supabase Realtime publish timed out") -> None:
        super().__init__(message=message, status_code=504, error_code="REALTIME_TIMEOUT")


class RealtimeRateLimitError(RealtimePublishError):
    """Raised when Realtime broadcast API rate limit is reached."""

    def __init__(self, message: str = "Supabase Realtime rate limit reached") -> None:
        super().__init__(message=message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")


class RealtimeQueuePayload(BaseModel):
    """Payload strictly restricted to token numbers, counts, and wait estimates (Rule 10).

    Guarantees:
    - Zero patient names, phones, or private clinical notes.
    """

    model_config = ConfigDict(extra="forbid")

    token_number: int | None = Field(default=None, description="Affected token sequence number")
    current_token: int | None = Field(default=None, description="Currently serving token number")
    total_waiting: int = Field(
        default=0, ge=0, description="Total patients currently waiting in queue"
    )
    estimated_wait_minutes: int | None = Field(
        default=None, ge=0, description="Estimated wait minutes"
    )
    event: str = Field(
        ..., description="Queue event type (token.created, token.called, queue.update)"
    )
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")

    @model_validator(mode="before")
    @classmethod
    def reject_pii(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in data:
                if key.lower() in FORBIDDEN_PII_FIELDS:
                    raise ValueError(
                        f"Rule 10 violation: PII field '{key}' is forbidden in Realtime broadcasts."
                    )
        return data


class SupabaseRealtimeClient:
    """Outbound HTTPS client publishing queue broadcasts to Supabase Realtime (I-002).

    Channels:
    - `queue:{clinic_id}:{doctor_id}` per PRD §13.3 and Architecture §3.3.

    Non-negotiable invariants:
    - Rule 10: Zero patient name or phone numbers in broadcasts.
    - Service key server-side only.
    - Graceful fallback: Publish failure logged; clients fall back to 15s polling.
    """

    def __init__(
        self,
        base_url: str | None = None,
        service_role_key: str | None = None,
        timeout_seconds: float = 4.0,
    ) -> None:
        self.base_url = (base_url or settings.supabase_url).rstrip("/")
        self.service_role_key = service_role_key or settings.supabase_service_role_key
        self.timeout_seconds = timeout_seconds

        # Idempotency cache to prevent duplicate broadcast delivery
        self._processed_broadcasts: dict[str, float] = {}

    def _headers(self) -> dict[str, str]:
        key = self.service_role_key or "anon"
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def broadcast_queue_update(
        self,
        clinic_id: uuid.UUID | str,
        doctor_id: uuid.UUID | str,
        event: str,
        token_number: int | None = None,
        current_token: int | None = None,
        total_waiting: int = 0,
        estimated_wait_minutes: int | None = None,
        idempotency_key: str | None = None,
        non_blocking: bool = True,
    ) -> dict[str, Any]:
        """Publish an anonymous queue update to `queue:{clinic_id}:{doctor_id}` channel."""
        from app.integrations.outage import vendor_outage_manager

        topic = f"queue:{clinic_id}:{doctor_id}"

        # 0. Check active vendor outage - activate defined degraded behavior
        if vendor_outage_manager.is_outage("realtime"):
            degraded = vendor_outage_manager.get_degraded_behavior("realtime")
            logger.warning(
                "Realtime broadcast suppressed: active vendor outage. Degraded fallback: %s",
                degraded,
            )
            if not non_blocking:
                raise RealtimePublishError(
                    message=f"Realtime publish failed: vendor outage active ({degraded.get('banner_text')})"
                )
            return {
                "status": "degraded_polling",
                "topic": topic,
                "degraded_behavior": degraded,
            }

        # 1. Idempotency duplicate check
        now = time.time()
        if idempotency_key:
            if idempotency_key in self._processed_broadcasts:
                expiry = self._processed_broadcasts[idempotency_key]
                if now < expiry:
                    logger.info(
                        "Duplicate Realtime broadcast suppressed for key %s", idempotency_key
                    )
                    return {
                        "status": "duplicate_suppressed",
                        "topic": f"queue:{clinic_id}:{doctor_id}",
                        "idempotency_key": idempotency_key,
                    }
            # Cache key for 5 minutes
            self._processed_broadcasts[idempotency_key] = now + 300.0

        # Clean expired keys
        self._processed_broadcasts = {
            k: exp for k, exp in self._processed_broadcasts.items() if exp > now
        }

        # 2. Construct and validate payload (enforces Rule 10)
        timestamp_str = datetime.now(UTC).isoformat()
        payload_obj = RealtimeQueuePayload(
            token_number=token_number,
            current_token=current_token,
            total_waiting=total_waiting,
            estimated_wait_minutes=estimated_wait_minutes,
            event=event,
            timestamp=timestamp_str,
        )

        topic = f"queue:{clinic_id}:{doctor_id}"
        message_body = {
            "messages": [
                {
                    "topic": topic,
                    "event": event,
                    "payload": payload_obj.model_dump(),
                }
            ]
        }

        endpoint = f"{self.base_url}/realtime/v1/api/broadcast"

        # 3. HTTPS publish
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(endpoint, json=message_body, headers=self._headers())

            if res.status_code == 429:
                logger.warning("Realtime broadcast rate limit reached on %s", topic)
                if not non_blocking:
                    raise RealtimeRateLimitError()
                return {"status": "rate_limited", "topic": topic}

            if res.status_code >= 400:
                logger.error(
                    "Realtime broadcast HTTP error %d on %s: %s",
                    res.status_code,
                    topic,
                    res.text,
                )
                await vendor_outage_manager.record_failure("realtime", f"HTTP {res.status_code}")
                if not non_blocking:
                    raise RealtimePublishError(
                        message=f"Realtime publish failed with HTTP {res.status_code}",
                        status_code=res.status_code,
                    )
                return {"status": "error", "status_code": res.status_code, "topic": topic}

            vendor_outage_manager.record_success("realtime")
            logger.info("Realtime queue update broadcasted to %s: %s", topic, event)
            return {
                "status": "published",
                "topic": topic,
                "event": event,
                "payload": payload_obj.model_dump(),
            }

        except httpx.TimeoutException as exc:
            logger.warning("Realtime broadcast timeout on %s: %s", topic, exc)
            await vendor_outage_manager.record_failure("realtime", "TimeoutException")
            if not non_blocking:
                raise RealtimeTimeoutError() from exc
            return {"status": "timeout_fallback_to_polling", "topic": topic}

        except Exception as exc:
            if isinstance(exc, RealtimePublishError):
                raise
            logger.error("Realtime publish unexpected error on %s: %s", topic, exc)
            await vendor_outage_manager.record_failure("realtime", str(exc))
            if not non_blocking:
                raise RealtimePublishError(message=str(exc)) from exc
            return {"status": "error_fallback_to_polling", "topic": topic, "detail": str(exc)}
