import pytest

from app.integrations.outage import vendor_outage_manager
from app.integrations.webhooks import webhook_idempotency_store


@pytest.fixture(autouse=True)
def reset_global_integration_state() -> None:
    """Ensure test isolation by resetting global integration singletons and failure states."""
    vendor_outage_manager.resolve_outage("realtime")
    vendor_outage_manager.resolve_outage("turnstile")
    vendor_outage_manager.resolve_outage("supabase_auth")
    vendor_outage_manager.resolve_outage("openrouter")
    vendor_outage_manager.clear_alerts()
    webhook_idempotency_store.clear()
