import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class VendorAuthError(Exception):
    """Base exception for vendor OAuth / token management errors."""

    def __init__(self, message: str, provider: str = "vendor") -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider


class VendorTokenRevokedError(VendorAuthError):
    """Raised when vendor refresh token has been revoked, requiring re-consent."""

    def __init__(
        self,
        message: str,
        provider: str,
        reconsent_url: str,
    ) -> None:
        super().__init__(message=message, provider=provider)
        self.reconsent_url = reconsent_url


@dataclass
class VendorToken:
    access_token: str
    refresh_token: str
    expires_at: float  # Unix timestamp
    token_type: str = "Bearer"
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        """Returns True if the token has expired or will expire within 30 seconds buffer."""
        return time.time() + 30.0 >= self.expires_at


class VendorTokenManager:
    """Manages vendor OAuth2 / API tokens with automatic proactive refresh

    and explicit re-consent recovery for revoked credentials (PRD §13, Task 46).
    """

    def __init__(
        self,
        provider: str,
        token_endpoint: str,
        client_id: str,
        client_secret: str,
        reconsent_path: str | None = None,
        initial_token: VendorToken | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.provider = provider
        self.token_endpoint = token_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.reconsent_url = reconsent_path or f"/api/v1/auth/vendor/{provider}/connect"
        self._token: VendorToken | None = initial_token
        self._http_client = http_client

    def set_token(self, token: VendorToken) -> None:
        self._token = token

    def get_current_token(self) -> VendorToken | None:
        return self._token

    async def get_valid_access_token(self) -> str:
        """Return a valid access token.

        If the current token is expired, automatically refreshes it via the vendor
        token endpoint without user action.
        If the token has been revoked, raises VendorTokenRevokedError with reconsent_url.
        """
        if not self._token:
            raise VendorTokenRevokedError(
                message=f"No active session for provider '{self.provider}'. Re-consent required.",
                provider=self.provider,
                reconsent_url=self.reconsent_url,
            )

        # Proactive refresh if expired or near expiry
        if self._token.is_expired:
            logger.info(
                f"Vendor token for '{self.provider}' expired; refreshing automatically without user action..."
            )
            await self.refresh_token()

        assert self._token is not None
        return self._token.access_token

    async def refresh_token(self) -> VendorToken:
        """Exchange the refresh token for a fresh access token."""
        if not self._token or not self._token.refresh_token:
            raise VendorTokenRevokedError(
                message="Cannot refresh: missing refresh token. Re-consent required.",
                provider=self.provider,
                reconsent_url=self.reconsent_url,
            )

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            if self._http_client:
                response = await self._http_client.post(self.token_endpoint, data=payload)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(self.token_endpoint, data=payload)

            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                new_token = VendorToken(
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token", self._token.refresh_token),
                    expires_at=time.time() + float(data.get("expires_in", 3600)),
                    token_type=data.get("token_type", "Bearer"),
                    scope=data.get("scope"),
                )
                self._token = new_token
                logger.info(f"Vendor token for '{self.provider}' refreshed successfully.")
                return new_token

            # Handle revoked / expired refresh token (OAuth RFC 6749 invalid_grant)
            error_data = {}
            try:
                error_data = response.json()
            except Exception:
                pass

            error_code = error_data.get("error", "")
            if response.status_code in (400, 401) and (
                error_code in ("invalid_grant", "unauthorized_client", "revoked_token")
                or "revoked" in str(error_data).lower()
                or "expired" in str(error_data).lower()
            ):
                logger.warning(
                    f"Vendor refresh token for '{self.provider}' was revoked or invalid: {error_data}"
                )
                self._token = None
                raise VendorTokenRevokedError(
                    message=f"Vendor token has been revoked by '{self.provider}'. Please re-authenticate.",
                    provider=self.provider,
                    reconsent_url=self.reconsent_url,
                )

            raise VendorAuthError(
                f"Failed to refresh vendor token (HTTP {response.status_code}): {response.text}",
                provider=self.provider,
            )

        except httpx.RequestError as exc:
            raise VendorAuthError(
                f"Network error while connecting to vendor '{self.provider}': {exc}",
                provider=self.provider,
            ) from exc
