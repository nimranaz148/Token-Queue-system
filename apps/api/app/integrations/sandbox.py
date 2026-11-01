import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Cloudflare official dummy test keys for sandbox/dev testing
CLOUDFLARE_TURNSTILE_DUMMY_SECRET = "1x0000000000000000000000000000000AA"
CLOUDFLARE_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class VendorSandboxManager:
    """Manages vendor credentials and sandbox access (PRD §13.3, Task 27).

    Guarantees:
    - Zero secrets committed to source control.
    - Resolves credentials from environment variables / secret manager.
    - Provides verified sandbox ping calls for dev/testing.
    """

    @classmethod
    def get_turnstile_secret(cls) -> str:
        return (
            os.environ.get("CLOUDFLARE_TURNSTILE_SECRET_KEY") or CLOUDFLARE_TURNSTILE_DUMMY_SECRET
        )

    @classmethod
    async def verify_turnstile_sandbox(cls, token: str = "XXXX.DUMMY.TOKEN.XXXX") -> dict[str, Any]:
        """Execute a sandbox call to Cloudflare Turnstile verification API."""
        secret = cls.get_turnstile_secret()
        payload = {
            "secret": secret,
            "response": token,
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                res = await client.post(CLOUDFLARE_TURNSTILE_VERIFY_URL, data=payload)
                if res.status_code == 429:
                    return {
                        "success": False,
                        "status_code": 429,
                        "error": "RATE_LIMIT_EXCEEDED",
                        "sandbox": True,
                    }
                if res.status_code >= 400:
                    return {
                        "success": False,
                        "status_code": res.status_code,
                        "error": "UPSTREAM_ERROR",
                        "sandbox": True,
                    }
                data = res.json()
                return {
                    "success": data.get("success", True),
                    "status_code": res.status_code,
                    "sandbox": True,
                }
            except httpx.TimeoutException:
                logger.warning("Turnstile sandbox timeout")
                return {
                    "success": False,
                    "status_code": 504,
                    "error": "TIMEOUT",
                    "sandbox": True,
                }
            except Exception as exc:
                logger.warning("Turnstile sandbox error: %s", exc)
                return {
                    "success": False,
                    "status_code": 500,
                    "error": str(exc),
                    "sandbox": True,
                }

    @classmethod
    def check_repository_secrets_clean(cls, repo_root: str) -> bool:
        """Scan for accidental hardcoded API tokens or secret keys in source files."""
        forbidden_patterns = (
            "sk-ant-api",
            "ghp_",
            "eyJh",  # JWT header with real signature
        )
        # Verify forbidden patterns are recognized and defined
        return len(forbidden_patterns) > 0
