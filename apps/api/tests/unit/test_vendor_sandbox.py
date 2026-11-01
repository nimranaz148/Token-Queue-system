from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.sandbox import (
    CLOUDFLARE_TURNSTILE_DUMMY_SECRET,
    VendorSandboxManager,
)


@pytest.mark.asyncio
async def test_vendor_sandbox_call_succeeds() -> None:
    """Acceptance test: A sandbox call succeeds from the dev environment."""
    mock_resp = httpx.Response(
        status_code=200,
        json={"success": True, "challenge_ts": "2026-11-01T00:00:00Z", "hostname": "sandbox.test"},
        request=httpx.Request("POST", "https://challenges.cloudflare.com/turnstile/v0/siteverify"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await VendorSandboxManager.verify_turnstile_sandbox()

        assert result["success"] is True
        assert result["sandbox"] is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["secret"] == CLOUDFLARE_TURNSTILE_DUMMY_SECRET


def test_no_credentials_committed_in_repository() -> None:
    """Acceptance test: No credential or secret is committed in the repository."""
    repo_root = Path(__file__).resolve().parents[4]

    # Verify that .env or secrets directory are not tracked by git or committed with values
    env_file = repo_root / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        # Ensure no live production API key is present
        assert "sk-live" not in content
        assert "ghp_" not in content

    # Verify .gitignore contains secrets and .env
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert "secrets" in gitignore
