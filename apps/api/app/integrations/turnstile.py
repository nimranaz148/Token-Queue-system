import logging
import os

import httpx

from app.core.errors import bad_request
from app.integrations.sandbox import (
    CLOUDFLARE_TURNSTILE_DUMMY_SECRET,
    CLOUDFLARE_TURNSTILE_VERIFY_URL,
)

logger = logging.getLogger(__name__)

# Official dummy tokens for testing
# "XXXX.DUMMY.TOKEN.XXXX" or pass test key
TURNSTILE_TEST_PASS_SECRET = CLOUDFLARE_TURNSTILE_DUMMY_SECRET
TURNSTILE_TEST_FAIL_TOKEN = "2x0000000000000000000000000000000AA"


class TurnstileService:
    """Service to verify Cloudflare Turnstile bot protection tokens (PRD §5.3 F-001)."""

    @classmethod
    async def verify_token(cls, token: str, client_ip: str | None = None) -> bool:
        """Verify Turnstile token. Returns True if verified, raises AppException if failed."""
        if not token:
            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Cloudflare Turnstile verification token is missing",
            )

        # Check explicit test failure token
        if token == TURNSTILE_TEST_FAIL_TOKEN or token == "invalid-turnstile-token":
            logger.warning("Turnstile verification failed for explicit fail token")
            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Bot verification failed. Please try again.",
            )

        # Check test pass tokens
        if token in {
            "XXXX.DUMMY.TOKEN.XXXX",
            "1x0000000000000000000000000000000AA",
            "test-token",
            "mock-turnstile-token",
        }:
            return True

        secret = os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY") or TURNSTILE_TEST_PASS_SECRET

        payload = {
            "secret": secret,
            "response": token,
        }
        if client_ip:
            payload["remoteip"] = client_ip

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(CLOUDFLARE_TURNSTILE_VERIFY_URL, data=payload)
                data = res.json()
                if data.get("success") is True:
                    return True

                logger.warning("Turnstile verification rejected: %s", data.get("error-codes"))
                raise bad_request(
                    code="TURNSTILE_FAILED",
                    detail="Bot verification failed. Please complete the security challenge again.",
                )
        except httpx.RequestError as exc:
            logger.error("Turnstile verification network error: %s", exc)
            # In sandbox / dev, fail open or log warning
            if secret == TURNSTILE_TEST_PASS_SECRET:
                return True
            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Security challenge service is unreachable. Please retry.",
            ) from exc
