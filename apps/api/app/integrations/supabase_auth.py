import logging
import time
from typing import Any

import httpx
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseAuthError(Exception):
    """Base exception for Supabase Auth integration failures."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "AUTH_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class SupabaseAuthTimeoutError(SupabaseAuthError):
    """Raised when Supabase Auth request times out, signalling retry eligibility."""

    def __init__(self, message: str = "Supabase Auth service timed out") -> None:
        super().__init__(message=message, status_code=504, error_code="AUTH_TIMEOUT")


class SupabaseAuthRateLimitError(SupabaseAuthError):
    """Raised when Supabase Auth or custom SMTP rate limit is reached."""

    def __init__(self, message: str = "Supabase Auth rate limit reached") -> None:
        super().__init__(message=message, status_code=429, error_code="RATE_LIMIT_EXCEEDED")


class SupabaseAuthClient:
    """External client for Supabase Auth service (PRD §13.3 I-001).

    Enforces:
    - Service key server-side only (never exposed to client).
    - Custom SMTP magic link delivery with retry handling.
    - 10-minute caching for JWKS / public keys.
    - Idempotency tracking against duplicate deliveries.
    """

    def __init__(
        self,
        base_url: str | None = None,
        service_role_key: str | None = None,
        jwt_secret: str | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.base_url = (base_url or settings.supabase_url).rstrip("/")
        self.service_role_key = service_role_key or settings.supabase_service_role_key
        self.jwt_secret = jwt_secret or settings.supabase_jwt_secret or settings.jwt_secret_key
        self.timeout_seconds = timeout_seconds

        # JWKS cache with 10-minute TTL (PRD §13.3)
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cached_at: float = 0.0
        self._jwks_ttl_seconds: float = 600.0  # 10 minutes

        # In-memory duplicate delivery tracking for idempotency keys
        self._processed_deliveries: dict[str, float] = {}

    def _headers(self) -> dict[str, str]:
        key = self.service_role_key or "anon"
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def send_magic_link(
        self,
        email: str,
        redirect_to: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Trigger Supabase Auth email magic link (PRD §5.3 F-012, §13.3 I-001).

        Handles idempotency, timeouts, rate limits, and error responses.
        """
        now = time.time()

        # Check duplicate delivery
        if idempotency_key:
            if idempotency_key in self._processed_deliveries:
                expiry = self._processed_deliveries[idempotency_key]
                if now < expiry:
                    logger.info("Duplicate magic link delivery suppressed for key %s", idempotency_key)
                    return {"status": "duplicate_suppressed", "email": email}

        url = f"{self.base_url}/auth/v1/magiclink"
        payload: dict[str, Any] = {"email": email}
        if redirect_to:
            payload["options"] = {"email_redirect_to": redirect_to}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.post(url, headers=self._headers(), json=payload)
            except httpx.TimeoutException as exc:
                logger.error("Supabase Auth timeout requesting %s: %s", url, exc)
                raise SupabaseAuthTimeoutError() from exc
            except httpx.RequestError as exc:
                logger.error("Supabase Auth connection error: %s", exc)
                raise SupabaseAuthError(f"Connection error: {exc}", status_code=502) from exc

        if response.status_code == 429:
            raise SupabaseAuthRateLimitError(response.text or "Rate limit exceeded")

        if response.status_code >= 400:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            msg = error_data.get("msg") or error_data.get("message") or response.text or f"HTTP {response.status_code}"
            logger.error("Supabase Auth error %d: %s", response.status_code, msg)
            raise SupabaseAuthError(message=msg, status_code=response.status_code)

        if idempotency_key:
            self._processed_deliveries[idempotency_key] = now + 900.0  # 15 minutes TTL

        return response.json() if response.content else {"status": "success"}

    async def get_jwks(self, force_refresh: bool = False) -> dict[str, Any]:
        """Fetch JWKS keys with 10-minute caching (PRD §13.3)."""
        now = time.time()
        if not force_refresh and self._jwks_cache and (now - self._jwks_cached_at < self._jwks_ttl_seconds):
            return self._jwks_cache

        url = f"{self.base_url}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                res = await client.get(url, headers={"apikey": self.service_role_key or "anon"})
                if res.status_code != 200:
                    raise SupabaseAuthError(f"Failed to fetch JWKS: HTTP {res.status_code}", status_code=res.status_code)
                self._jwks_cache = res.json()
                self._jwks_cached_at = now
                return self._jwks_cache
            except httpx.TimeoutException as exc:
                raise SupabaseAuthTimeoutError("JWKS fetch timed out") from exc
            except httpx.RequestError as exc:
                raise SupabaseAuthError(f"JWKS connection error: {exc}", status_code=502) from exc

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify Supabase JWT token using symmetric secret or public claims."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise SupabaseAuthError("Session expired, please login again", status_code=401, error_code="TOKEN_EXPIRED") from exc
        except jwt.InvalidTokenError as exc:
            raise SupabaseAuthError("Invalid session token", status_code=401, error_code="INVALID_TOKEN") from exc
