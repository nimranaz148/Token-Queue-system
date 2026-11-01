import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.errors import AppException
from app.integrations.outage import VendorOutageManager, VendorStatus, vendor_outage_manager
from app.integrations.realtime import SupabaseRealtimeClient
from app.integrations.sentry import SentryClient
from app.integrations.turnstile import TurnstileService


@pytest.fixture(autouse=True)
def reset_outage_manager() -> None:
    vendor_outage_manager.resolve_outage("realtime")
    vendor_outage_manager.resolve_outage("turnstile")
    vendor_outage_manager.resolve_outage("supabase_auth")
    vendor_outage_manager.resolve_outage("openrouter")
    vendor_outage_manager.clear_alerts()


@pytest.mark.asyncio
async def test_forced_realtime_outage_shows_degraded_behaviour_and_raises_alert() -> None:
    """Acceptance criteria: A forced vendor outage shows the defined degraded behaviour and raises an alert."""
    mock_sentry = SentryClient()
    mock_sentry.capture_message = AsyncMock(return_value={"status": "buffered"})  # type: ignore[method-assign]

    manager = VendorOutageManager(sentry_client=mock_sentry)

    # 1. Force the vendor outage
    alert = await manager.force_vendor_outage(
        "realtime", reason="Primary Supabase Realtime cluster unreachable"
    )

    # 2. Check alert was raised and sent to Sentry
    assert alert["vendor"] == "realtime"
    assert alert["status"] == VendorStatus.OUTAGE
    assert alert["reason"] == "Primary Supabase Realtime cluster unreachable"

    mock_sentry.capture_message.assert_called_once()
    call_kwargs = mock_sentry.capture_message.call_args[1]
    assert call_kwargs["level"] == "fatal"
    assert call_kwargs["tags"]["vendor"] == "realtime"
    assert call_kwargs["tags"]["outage"] == "true"
    assert "VENDOR_OUTAGE_ALERT" in call_kwargs["message"]

    # 3. Check defined degraded behaviour: 5s polling fallback without blocking operations
    degraded = manager.get_degraded_behavior("realtime")
    assert degraded["mode"] == "polling"
    assert degraded["polling_interval_seconds"] == 5
    assert degraded["websocket_enabled"] is False
    assert degraded["booking_unaffected"] is True

    # 4. End-to-end integration: broadcast returns degraded polling status
    # Set global manager outage to test Realtime client
    await vendor_outage_manager.force_vendor_outage("realtime", reason="Global cluster drill")
    client = SupabaseRealtimeClient(
        base_url="https://mock.supabase.co", service_role_key="mock_key"
    )

    res = await client.broadcast_queue_update(
        clinic_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        event="token.called",
        token_number=101,
        current_token=101,
    )

    assert res["status"] == "degraded_polling"
    assert res["degraded_behavior"]["mode"] == "polling"
    assert res["degraded_behavior"]["polling_interval_seconds"] == 5


@pytest.mark.asyncio
async def test_forced_turnstile_outage_fails_closed_public_booking_leaves_reception_unaffected() -> (
    None
):
    """Acceptance criteria: Turnstile outage shows defined degraded behaviour (fail closed public, reception unaffected)."""
    # 1. Force Turnstile outage
    alert = await vendor_outage_manager.force_vendor_outage(
        "turnstile", reason="Cloudflare edge API outage"
    )

    assert alert["status"] == VendorStatus.OUTAGE
    assert len(vendor_outage_manager.get_recent_alerts()) > 0

    # 2. Check defined degraded behaviour
    degraded = vendor_outage_manager.get_degraded_behavior("turnstile")
    assert degraded["public_booking_allowed"] is False
    assert degraded["reception_walk_in_allowed"] is True
    assert degraded["fail_mode"] == "fail_closed_public_only"

    # 3. Attempting public verification raises TURNSTILE_OUTAGE
    with pytest.raises(AppException) as exc_info:
        await TurnstileService.verify_token("any-token")

    assert exc_info.value.code == "TURNSTILE_OUTAGE"
    assert "Online booking verification is temporarily unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_consecutive_failure_threshold_automatically_triggers_outage_and_alert() -> None:
    """Consecutive failures trip the circuit breaker and raise an outage alert."""
    mock_sentry = SentryClient()
    mock_sentry.capture_message = AsyncMock(return_value={"status": "buffered"})  # type: ignore[method-assign]

    manager = VendorOutageManager(sentry_client=mock_sentry)

    # 2 failures do not trip
    await manager.record_failure("realtime", "504 Gateway Timeout")
    await manager.record_failure("realtime", "504 Gateway Timeout")
    assert manager.is_outage("realtime") is False
    mock_sentry.capture_message.assert_not_called()

    # 3rd failure trips threshold
    await manager.record_failure("realtime", "504 Gateway Timeout", failure_threshold=3)
    assert manager.is_outage("realtime") is True
    mock_sentry.capture_message.assert_called_once()
    assert len(manager.get_recent_alerts()) == 1


@pytest.mark.asyncio
async def test_vendor_outage_resolution_restores_operational_status() -> None:
    """Resolving vendor outage resets status to OPERATIONAL."""
    await vendor_outage_manager.force_vendor_outage("realtime", reason="Maintenance window")
    assert vendor_outage_manager.is_outage("realtime") is True

    vendor_outage_manager.resolve_outage("realtime")
    assert vendor_outage_manager.is_outage("realtime") is False
    assert vendor_outage_manager.get_status("realtime") == VendorStatus.OPERATIONAL
