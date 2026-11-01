from pathlib import Path


def test_vendor_integrations_skill_cites_documentation_and_date() -> None:
    """Acceptance test: The integration skill cites vendor documentation URL and date (Task 28)."""
    repo_root = Path(__file__).resolve().parents[4]
    skill_file = repo_root / ".agent" / "skills" / "vendor-integrations" / "SKILL.md"

    assert skill_file.exists(), "vendor-integrations SKILL.md must exist in .agent/skills"

    content = skill_file.read_text(encoding="utf-8")

    # Assert required vendor documentation URLs
    assert "https://supabase.com/docs/guides/auth" in content
    assert "https://developers.cloudflare.com/turnstile/get-started/server-side-validation/" in content
    assert "https://docs.sentry.io/platforms/python/guides/fastapi/" in content
    assert "https://supabase.com/docs/guides/realtime" in content

    # Assert documentation date citation
    assert "2026-10-31" in content
    assert "Documentation Retrieval Date" in content
