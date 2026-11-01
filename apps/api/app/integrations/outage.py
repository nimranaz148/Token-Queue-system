import enum
import logging
from datetime import UTC, datetime
from typing import Any

from app.integrations.sentry import SentryClient

logger = logging.getLogger(__name__)


class VendorStatus(enum.StrEnum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OUTAGE = "outage"


class VendorOutageManager:
    """Manages vendor service health, circuit breaking, degraded fallbacks, and alerts (PRD §13.3, Task 49).

    Acceptance:
    - A forced vendor outage shows the defined degraded behaviour and raises an alert.
    """

    def __init__(self, sentry_client: SentryClient | None = None) -> None:
        self.sentry_client = sentry_client or SentryClient()
        self._vendor_status: dict[str, VendorStatus] = {
            "realtime": VendorStatus.OPERATIONAL,
            "turnstile": VendorStatus.OPERATIONAL,
            "supabase_auth": VendorStatus.OPERATIONAL,
            "openrouter": VendorStatus.OPERATIONAL,
        }
        self._consecutive_failures: dict[str, int] = {}
        self._outage_reasons: dict[str, str] = {}
        self._alerts_sent: list[dict[str, Any]] = []

    def is_outage(self, vendor: str) -> bool:
        """Check if a vendor is currently in forced or detected outage."""
        return self._vendor_status.get(vendor) == VendorStatus.OUTAGE

    def is_degraded(self, vendor: str) -> bool:
        """Check if a vendor is currently degraded or in outage."""
        status = self._vendor_status.get(vendor, VendorStatus.OPERATIONAL)
        return status in (VendorStatus.DEGRADED, VendorStatus.OUTAGE)

    def get_status(self, vendor: str) -> VendorStatus:
        """Get current health status of a vendor."""
        return self._vendor_status.get(vendor, VendorStatus.OPERATIONAL)

    async def force_vendor_outage(
        self, vendor: str, reason: str = "Simulated vendor outage drill"
    ) -> dict[str, Any]:
        """Force a vendor into OUTAGE state, activate degraded behavior, and raise an alert."""
        self._vendor_status[vendor] = VendorStatus.OUTAGE
        self._outage_reasons[vendor] = reason
        timestamp = datetime.now(UTC).isoformat()

        logger.critical(
            "CRITICAL: Forced vendor outage activated for '%s'. Reason: %s",
            vendor,
            reason,
        )

        alert_payload = {
            "vendor": vendor,
            "status": VendorStatus.OUTAGE,
            "reason": reason,
            "timestamp": timestamp,
            "degraded_behavior": self.get_degraded_behavior(vendor),
        }
        self._alerts_sent.append(alert_payload)

        # Dispatch alert to Sentry
        try:
            await self.sentry_client.capture_message(
                message=f"VENDOR_OUTAGE_ALERT: Vendor '{vendor}' experienced forced outage: {reason}",
                level="fatal",
                extra=alert_payload,
                tags={"vendor": vendor, "outage": "true", "tier": "p0"},
            )
        except Exception as exc:
            logger.error("Failed to send outage alert to Sentry: %s", exc)

        return alert_payload

    def resolve_outage(self, vendor: str) -> None:
        """Restore vendor to OPERATIONAL state and clear failure counters."""
        logger.info("Vendor '%s' outage resolved. Restoring operational status.", vendor)
        self._vendor_status[vendor] = VendorStatus.OPERATIONAL
        self._consecutive_failures[vendor] = 0
        if vendor in self._outage_reasons:
            del self._outage_reasons[vendor]

    def get_degraded_behavior(self, vendor: str) -> dict[str, Any]:
        """Return the PRD-defined degraded fallback behavior for a given vendor."""
        if vendor == "realtime":
            # PRD §13.3 I-002: Publish failure logged; clients fall back to polling
            return {
                "mode": "polling",
                "polling_interval_seconds": 5,
                "websocket_enabled": False,
                "banner_text": "Live queue updates temporarily degraded: auto-refreshing every 5 seconds.",
                "booking_unaffected": True,
            }
        elif vendor == "turnstile":
            # PRD §13.3 I-003: Fail closed on public booking; reception unaffected
            return {
                "public_booking_allowed": False,
                "reception_walk_in_allowed": True,
                "banner_text": "Online booking verification is temporarily unavailable. Walk-in queue at clinic remains open.",
                "fail_mode": "fail_closed_public_only",
            }
        elif vendor == "supabase_auth":
            # PRD §13.3 I-001: Show retry; JWKS cached 10 min
            return {
                "magic_link_dispatch": False,
                "jwks_cache_enabled": True,
                "banner_text": "Authentication service is degraded. Existing sessions remain valid; retry in 2 minutes.",
            }
        elif vendor == "openrouter":
            # PRD §13.3 I-004: Timeout 20 s -> Gemini fallback
            return {
                "fallback_provider": "gemini",
                "ai_notes_enabled": True,
                "banner_text": "AI provider degraded. Switched to backup provider.",
            }
        return {
            "mode": "generic_degraded",
            "banner_text": f"Service '{vendor}' is experiencing degraded performance.",
        }

    async def record_failure(
        self,
        vendor: str,
        error_message: str,
        failure_threshold: int = 3,
    ) -> None:
        """Record a failure against a vendor and trigger automatic outage & alert if threshold is reached."""
        count = self._consecutive_failures.get(vendor, 0) + 1
        self._consecutive_failures[vendor] = count
        logger.warning(
            "Vendor '%s' recorded failure #%d: %s",
            vendor,
            count,
            error_message,
        )

        if count >= failure_threshold and not self.is_outage(vendor):
            await self.force_vendor_outage(
                vendor=vendor,
                reason=f"Exceeded failure threshold ({count} consecutive errors). Last error: {error_message}",
            )

    def record_success(self, vendor: str) -> None:
        """Reset consecutive failures upon successful vendor response."""
        self._consecutive_failures[vendor] = 0

    def get_recent_alerts(self) -> list[dict[str, Any]]:
        """Return audit list of generated vendor outage alerts."""
        return list(self._alerts_sent)

    def clear_alerts(self) -> None:
        """Clear alerts for testing."""
        self._alerts_sent.clear()


# Global vendor outage manager
vendor_outage_manager = VendorOutageManager()
