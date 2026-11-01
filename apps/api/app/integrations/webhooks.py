import hashlib
import hmac
import logging
import time

logger = logging.getLogger(__name__)


class WebhookVerifier:
    """HMAC-SHA256 signature verification for external vendor webhooks (PRD §13, Task 48)."""

    @staticmethod
    def compute_signature(secret: str, raw_body: bytes) -> str:
        """Compute the hex HMAC-SHA256 digest of raw body bytes."""
        return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    @classmethod
    def verify_signature(cls, secret: str, raw_body: bytes, signature_header: str | None) -> bool:
        """Verify incoming webhook signature using constant-time comparison to prevent timing attacks."""
        if not signature_header or not secret:
            return False

        # Support 'sha256=' prefix if provided by standard webhook providers (GitHub, Stripe, etc.)
        expected_sig = signature_header.replace("sha256=", "").strip()
        computed_sig = cls.compute_signature(secret, raw_body)

        return hmac.compare_digest(expected_sig.lower(), computed_sig.lower())


class WebhookIdempotencyStore:
    """In-memory idempotency store with TTL tracking against replayed webhook events."""

    def __init__(self, default_ttl_seconds: float = 86400.0) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._processed_events: dict[str, float] = {}

    def is_processed(self, event_id: str) -> bool:
        """Check if an event ID has already been processed and its record has not expired."""
        now = time.time()
        expiry = self._processed_events.get(event_id)
        if expiry is None:
            return False
        if now > expiry:
            del self._processed_events[event_id]
            return False
        return True

    def mark_processed(self, event_id: str, ttl_seconds: float | None = None) -> None:
        """Record an event ID as successfully processed."""
        ttl = ttl_seconds or self.default_ttl_seconds
        self._processed_events[event_id] = time.time() + ttl

    def clear(self) -> None:
        """Clear the store for testing."""
        self._processed_events.clear()


# Global idempotency instance
webhook_idempotency_store = WebhookIdempotencyStore()
