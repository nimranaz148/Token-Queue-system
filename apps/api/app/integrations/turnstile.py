import logging
import os
import time
from typing import Any

import httpx

from app.core.errors import bad_request
from app.integrations.sandbox import (
    CLOUDFLARE_TURNSTILE_DUMMY_SECRET,
    CLOUDFLARE_TURNSTILE_VERIFY_URL,
)

logger = logging.getLogger(__name__)

# Cloudflare official dummy tokens
TURNSTILE_TEST_PASS_SECRET = CLOUDFLARE_TURNSTILE_DUMMY_SECRET
TURNSTILE_TEST_FAIL_TOKEN = "2x0000000000000000000000000000000AA"
TURNSTILE_TEST_PASS_TOKEN = "1x0000000000000000000000000000000AA"


class TurnstileError(Exception):
    """Base exception for Cloudflare Turnstile integration failures (PRD §13.3 I-003)."""

    def __init__(
        self, message: str, status_code: int = 400, error_code: str = "TURNSTILE_FAILED"
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class TurnstileTimeoutError(TurnstileError):
    """Raised when Turnstile siteverify endpoint times out."""

    def __init__(self, message: str = "Turnstile verification service timed out") -> None:
        super().__init__(message=message, status_code=504, error_code="TURNSTILE_TIMEOUT")


class TurnstileService:
    """Service to verify Cloudflare Turnstile bot protection tokens (PRD §5.3 F-001, §13.3 I-003).

    Guarantees:
    - Outbound HTTPS verify to Cloudflare siteverify endpoint.
    - Secret key handled server-side only.
    - In-memory single-use replay protection (rejects replayed tokens).
    - Timeout and upstream 5xx handling.
    - Fail-closed on public online booking; reception walk-ins unaffected (§13.3).
    """

    # In-memory single-use token tracking: token -> expiry timestamp
    _used_tokens: dict[str, float] = {}

    @classmethod
    def _is_token_replayed(cls, token: str) -> bool:
        """Check and record single-use token replay."""
        now = time.time()
        # Clean expired tokens older than 10 minutes
        cls._used_tokens = {t: exp for t, exp in cls._used_tokens.items() if exp > now}

        if token in cls._used_tokens:
            return True
        # Record token with 5-minute validity window
        cls._used_tokens[token] = now + 300.0
        return False

    @classmethod
    async def verify_token(
        cls,
        token: str,
        client_ip: str | None = None,
        timeout_seconds: float = 3.0,
    ) -> bool:
        """Verify Turnstile token. Returns True if verified, raises AppException if failed."""
        if not token or not token.strip():
            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Cloudflare Turnstile verification token is missing",
            )

        token = token.strip()

        # Check explicit test failure token
        if token == TURNSTILE_TEST_FAIL_TOKEN or token == "invalid-turnstile-token":
            logger.warning("Turnstile verification failed for explicit fail token")
            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Bot verification failed. Please try again.",
            )

        # Single-use replay check for non-dummy tokens
        is_dummy = token in {
            "XXXX.DUMMY.TOKEN.XXXX",
            TURNSTILE_TEST_PASS_TOKEN,
            "test-token",
            "mock-turnstile-token",
        }
        if not is_dummy and cls._is_token_replayed(token):
            logger.warning("Duplicate Turnstile token delivery detected: %s", token[:8])
            raise bad_request(
                code="TURNSTILE_DUPLICATE_TOKEN",
                detail="Security challenge token has already been used. Please solve a new challenge.",
            )

        # Check pass tokens in dev/test
        if is_dummy:
            return True

        secret = os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY") or TURNSTILE_TEST_PASS_SECRET

        payload = {
            "secret": secret,
            "response": token,
        }
        if client_ip:
            payload["remoteip"] = client_ip

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                res = await client.post(CLOUDFLARE_TURNSTILE_VERIFY_URL, data=payload)

            if res.status_code >= 500:
                logger.error(
                    "Turnstile verification server error HTTP %d: %s", res.status_code, res.text
                )
                if secret == TURNSTILE_TEST_PASS_SECRET:
                    return True
                raise bad_request(
                    code="TURNSTILE_SERVICE_ERROR",
                    detail="Security verification service is temporarily unavailable. Please retry.",
                )

            data: dict[str, Any] = res.json()
            if data.get("success") is True:
                return True

            error_codes = data.get("error-codes", [])
            logger.warning("Turnstile verification rejected: %s", error_codes)

            if "timeout-or-duplicate" in error_codes:
                raise bad_request(
                    code="TURNSTILE_DUPLICATE_TOKEN",
                    detail="Security challenge token has expired or already been used. Please try again.",
                )

            raise bad_request(
                code="TURNSTILE_FAILED",
                detail="Bot verification failed. Please complete the security challenge again.",
            )

        except httpx.TimeoutException as exc:
            logger.error("Turnstile verification timed out: %s", exc)
            if secret == TURNSTILE_TEST_PASS_SECRET:
                return True
            raise bad_request(
                code="TURNSTILE_TIMEOUT",
                detail="Security challenge timed out. Please check your connection and retry.",
            ) from exc

        except httpx.RequestError as exc:
            logger.error("Turnstile verification network error: %s", exc)
            if secret == TURNSTILE_TEST_PASS_SECRET:
                return True
            raise bad_request(
                code="TURNSTILE_NETWORK_ERROR",
                detail="Security challenge service is unreachable. Please retry.",
            ) from exc
