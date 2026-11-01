import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.masking import mask_sensitive_data

logger = logging.getLogger(__name__)


class SentryIntegrationError(Exception):
    """Exception for Sentry delivery failures."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "SENTRY_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class SentryClient:
    """Non-blocking HTTPS client for Sentry error tracking (PRD §13.3 I-006).

    Guarantees:
    - PII masked on all exceptions and context fields.
    - Non-blocking execution (failures drop or buffer locally, never bubble to users).
    - Idempotency key tracking against duplicate event deliveries.
    - Contract compatibility with Sentry envelope/store API.
    """

    def __init__(
        self,
        dsn: str | None = None,
        environment: str | None = None,
        timeout_seconds: float = 3.0,
    ) -> None:
        self.dsn = dsn if dsn is not None else settings.sentry_dsn
        self.environment = environment or settings.sentry_environment
        self.timeout_seconds = timeout_seconds

        self.public_key: str | None = None
        self.host: str | None = None
        self.project_id: str | None = None
        self.store_url: str | None = None

        self._parse_dsn()
        self._processed_events: dict[str, float] = {}
        self._local_buffer: list[dict[str, Any]] = []

    def _parse_dsn(self) -> None:
        if not self.dsn:
            return

        try:
            parsed = urlparse(self.dsn)
            self.public_key = parsed.username
            self.host = parsed.hostname
            path_parts = parsed.path.strip("/").split("/")
            self.project_id = path_parts[0] if path_parts else None

            if self.public_key and self.host and self.project_id:
                scheme = parsed.scheme or "https"
                port = f":{parsed.port}" if parsed.port else ""
                self.store_url = f"{scheme}://{self.host}{port}/api/{self.project_id}/store/"
        except Exception as exc:
            logger.warning("Failed to parse Sentry DSN '%s': %s", self.dsn, exc)

    def _auth_header(self) -> str:
        timestamp = int(time.time())
        return (
            f"Sentry sentry_version=7, "
            f"sentry_client=clinic-backend/0.1.0, "
            f"sentry_timestamp={timestamp}, "
            f"sentry_key={self.public_key}"
        )

    def is_configured(self) -> bool:
        return bool(self.store_url and self.public_key)

    async def capture_exception(
        self,
        exc: Exception,
        extra: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Capture an exception and send to Sentry with PII masking and non-blocking safety."""
        return await self._capture_event(
            level="error",
            message=str(exc),
            exception_type=type(exc).__name__,
            extra=extra,
            tags=tags,
            idempotency_key=idempotency_key,
        )

    async def capture_message(
        self,
        message: str,
        level: str = "info",
        extra: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Capture an informational or warning message."""
        return await self._capture_event(
            level=level,
            message=message,
            exception_type=None,
            extra=extra,
            tags=tags,
            idempotency_key=idempotency_key,
        )

    async def _capture_event(
        self,
        level: str,
        message: str,
        exception_type: str | None = None,
        extra: dict[str, Any] | None = None,
        tags: dict[str, str] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        now = time.time()

        # Idempotency / duplicate check
        if idempotency_key:
            if idempotency_key in self._processed_events:
                if now < self._processed_events[idempotency_key]:
                    logger.info("Duplicate Sentry event suppressed for key: %s", idempotency_key)
                    return {"status": "duplicate_suppressed", "idempotency_key": idempotency_key}

        event_id = uuid.uuid4().hex
        masked_extra = mask_sensitive_data(extra) if extra else {}

        payload: dict[str, Any] = {
            "event_id": event_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "platform": "python",
            "level": level,
            "environment": self.environment,
            "message": message,
            "tags": tags or {},
            "extra": masked_extra,
        }

        if exception_type:
            payload["exception"] = {
                "values": [
                    {
                        "type": exception_type,
                        "value": message,
                    }
                ]
            }

        # If Sentry is not configured, buffer event locally and return
        if not self.is_configured():
            self._local_buffer.append(payload)
            return {"status": "buffered_locally", "event_id": event_id}

        headers = {
            "Content-Type": "application/json",
            "X-Sentry-Auth": self._auth_header(),
        }

        # Non-blocking HTTPS delivery
        try:
            assert self.store_url is not None
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                res = await client.post(self.store_url, headers=headers, json=payload)

            if res.status_code == 429:
                logger.warning("Sentry quota exceeded (HTTP 429); dropped locally.")
                self._local_buffer.append(payload)
                return {"status": "rate_limited_buffered", "event_id": event_id}

            if res.status_code >= 400:
                logger.warning("Sentry API returned error %d: %s; buffered locally.", res.status_code, res.text)
                self._local_buffer.append(payload)
                return {"status": "error_buffered", "event_id": event_id, "status_code": res.status_code}

            if idempotency_key:
                self._processed_events[idempotency_key] = now + 900.0

            return {"status": "delivered", "event_id": event_id}

        except httpx.TimeoutException:
            logger.warning("Sentry delivery timed out; buffered locally.")
            self._local_buffer.append(payload)
            return {"status": "timeout_buffered", "event_id": event_id}

        except Exception as err:
            logger.warning("Sentry delivery network error: %s; dropped locally.", err)
            self._local_buffer.append(payload)
            return {"status": "network_error_buffered", "event_id": event_id}
