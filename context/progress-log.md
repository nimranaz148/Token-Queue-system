# Progress Log

Append-only history. Never edit or delete a line. The short status lives in `progress-tracker.md`; this file is where finished work, decisions and rulings are recorded, one dated line each, newest at the bottom. Agents read the tracker every session and this log only when they need history.

<!-- one line per event: YYYY-MM-DD — task NN done | decision | ruling — what and why -->
2026-10-31 — Task 00 done: Architecture Decision Record (docs/adr/0001-stack-decision.md) signed off per PRD §3.1.
2026-10-31 — Task 01 done: Repo scaffold (apps/api, apps/web, packages/api-client, infra, .env.example) and verification fast tier passed.
2026-10-31 — Task 02 done: CI/CD workflows (.github/workflows/*) verified per lane with verify.sh, security scan, and dependabot.
2026-10-31 — Task 03 done: PostgreSQL database foundation with 19 domain models (PRD §12.2-§12.3), Alembic migration 0001, and unit tests passing.
2026-10-31 — Task 04 done: Authentication & authorization skeleton, JWT security, RFC 7807 problem details, PRD §14.2 role matrix enforcement, and fast-tier verification passed.
2026-10-31 — Task 05 done: Central tenancy enforcement via SQLAlchemy event hooks, deny-by-default filter (0 rows without context), cross-tenant isolation, and automated tests passing.
2026-10-31 — Task 06 done: Immutable audit infrastructure, masking for sensitive personal/health data and IP hashing, covering all 29 PRD §14.1 audited actions with passing unit tests.
2026-10-31 — Task 07 done: API conventions enforced (/api/v1 versioned prefix, RFC 7807 problem details), OpenAPI client regenerated, and contract drift check passed.
