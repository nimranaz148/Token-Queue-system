import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.integrations.webhooks import WebhookVerifier, webhook_idempotency_store
from app.main import app


@pytest.fixture(autouse=True)
def reset_idempotency_store() -> None:
    webhook_idempotency_store.clear()


@pytest.mark.asyncio
async def test_webhook_bad_signature_rejected() -> None:
    """Acceptance criteria: a bad signature is rejected."""
    payload = json.dumps(
        {"id": "evt_test_bad_sig", "event": "customer.subscription.updated"}
    ).encode("utf-8")
    bad_signature = "invalid_signature_hex_12345"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": bad_signature,
                "X-Webhook-Event-Id": "evt_test_bad_sig",
            },
        )

    assert response.status_code == 400
    assert "Invalid or missing webhook signature" in response.text


@pytest.mark.asyncio
async def test_webhook_missing_signature_rejected() -> None:
    """Rejects webhook requests without signature header."""
    payload = json.dumps({"id": "evt_test_no_sig"}).encode("utf-8")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 400
    assert "Invalid or missing webhook signature" in response.text


@pytest.mark.asyncio
async def test_webhook_valid_signature_processed() -> None:
    """Acceptance criteria: valid signature processes new event successfully."""
    payload = json.dumps({"id": "evt_test_valid_001", "event": "payment.succeeded"}).encode("utf-8")
    valid_sig = WebhookVerifier.compute_signature(settings.webhook_secret, payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": f"sha256={valid_sig}",
                "X-Webhook-Event-Id": "evt_test_valid_001",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert data["event_id"] == "evt_test_valid_001"
    assert webhook_idempotency_store.is_processed("evt_test_valid_001") is True


@pytest.mark.asyncio
async def test_webhook_replayed_event_ignored() -> None:
    """Acceptance criteria: A replayed event is ignored."""
    payload = json.dumps({"id": "evt_test_replay_002", "event": "alert.triggered"}).encode("utf-8")
    valid_sig = WebhookVerifier.compute_signature(settings.webhook_secret, payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First delivery -> processed
        res1 = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": valid_sig,
                "X-Webhook-Event-Id": "evt_test_replay_002",
            },
        )
        assert res1.status_code == 200
        assert res1.json()["status"] == "processed"

        # Second delivery (replay with identical event id) -> ignored
        res2 = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": valid_sig,
                "X-Webhook-Event-Id": "evt_test_replay_002",
            },
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["status"] == "ignored"
        assert data2["event_id"] == "evt_test_replay_002"
        assert data2["detail"] == "Replayed event ignored"


@pytest.mark.asyncio
async def test_webhook_extracts_event_id_from_body_payload() -> None:
    """Event ID extracted from JSON body when header is absent."""
    payload = json.dumps({"id": "evt_body_payload_999", "type": "invoice.paid"}).encode("utf-8")
    valid_sig = WebhookVerifier.compute_signature(settings.webhook_secret, payload)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/webhooks/vendor",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Signature": valid_sig,
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert response.json()["event_id"] == "evt_body_payload_999"
