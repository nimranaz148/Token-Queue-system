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
2026-10-31 — Task 08 done: UI foundation, design tokens, FormShell mandated layout, DataGrid 4-state table, LayoutShell, and ui-registry updated.
2026-10-31 — Task 09 done: Agent service skeleton in apps/api/app/ai, zero DB credentials, tool catalog wired to domain services with caller identity and tenant scoping, provider fallback, and passing architecture/unit tests.
2026-10-31 — Task 10 done: Vertical slice connecting Web UI (LayoutShell, FormShell, DataGrid), FastAPI router (/api/v1/admin/clinics), ClinicService, Postgres DB, immutable audit logging, and generated TypeScript client with passing verification.
2026-11-01 — Task 11 done: Staff Login (F-012) implemented with FormShell UI, email format validation, 5 req/hr rate limiting, anti-enumeration identical response, multi-clinic tenant choice/switch (/me/active-clinic), audit logging, and 0 contract drift.
2026-11-01 — Task 12 done: New Clinic onboarding (F-013) with FormShell UI at /admin/clinics/new, field validation (slug regex, email, name), atomic provisioning of clinic, settings, and owner member, dual audit logs (clinic.create, member.invite), and 0 contract drift.
2026-11-01 — Task 13 done: Clinics List (F-014) with DataGrid UI at /admin/clinics, search filtering, doctors count and 7d tokens telemetry subqueries, audited status management modal with mandatory reason, and full fast-tier verification passed.
2026-11-01 — Task 14 done: Staff Management (F-015) with MemberService, API endpoints (/api/v1/members), owner role guard, unique clinic email enforcement, doctor linkage validation, audit logging (member.invite, member.role_change, member.deactivate), DataGrid UI at /settings/staff, and fast-tier verification passed.
2026-11-01 — Task 15 done: Supabase Auth integration (I-001) implemented with server-side service key, custom SMTP magic link dispatch, 10-minute cached JWKS retrieval, idempotency suppression for duplicate deliveries, timeout/error handling, and passing contract test suite.
2026-11-01 — Task 16 done: Sentry error tracking integration (I-006) implemented with DSN configuration, PII masking on extra/exception payloads, non-blocking execution with local buffering, duplicate delivery suppression, and passing contract test suite.
2026-11-01 — Task 17 done: Scaffold web app pack verified with Next.js Turbopack production build, strict TypeScript (0 errors), ESLint (0 errors), 34 passing Vitest tests, and static route generation for all 7 routes.
