import json
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.integrations.webhooks import WebhookVerifier, webhook_idempotency_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/vendor", status_code=status.HTTP_200_OK)
async def handle_vendor_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
    x_webhook_event_id: str | None = Header(None, alias="X-Webhook-Event-Id"),
) -> dict[str, Any]:
    """Handle incoming external vendor webhook events with HMAC signature verification and idempotency.

    Acceptance:
    - A replayed event is ignored (status 200 with status: ignored)
    - A bad signature is rejected (status 400 Bad Request)
    """
    raw_body = await request.body()

    # 1. Signature verification
    secret = settings.webhook_secret
    if not x_webhook_signature or not WebhookVerifier.verify_signature(
        secret, raw_body, x_webhook_signature
    ):
        logger.warning("Rejected webhook with invalid or missing signature")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or missing webhook signature.",
        )

    # 2. Extract event_id from header or JSON body
    event_id = x_webhook_event_id
    if not event_id:
        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            event_id = payload.get("id") or payload.get("event_id")
        except Exception:
            event_id = None

    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event ID in headers or payload.",
        )

    # 3. Idempotency check: A replayed event is ignored
    if webhook_idempotency_store.is_processed(event_id):
        logger.info("Ignoring replayed webhook event: %s", event_id)
        return {
            "status": "ignored",
            "event_id": event_id,
            "detail": "Replayed event ignored",
        }

    # 4. Mark processed and return
    webhook_idempotency_store.mark_processed(event_id)
    logger.info("Successfully processed webhook event: %s", event_id)
    return {
        "status": "processed",
        "event_id": event_id,
        "detail": "Event processed successfully",
    }
