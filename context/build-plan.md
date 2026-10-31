# Build Plan

> Generated from `docs/prd/PRD.md` (v0.2.2, profile `production`) by Honey's Spec Harness. This is a living document: edit it freely; the PRD stays the source for scope.

## Core Principle

Full-page UI built with mock data first and verified visually before any logic is written; then functionality is wired step by step. Every feature is visible and testable before the next one starts. No invisible backend phases.

Every task cites its **feature ID** (F-, D-, R-, W-, I-xxx) or PRD section. Never invent a business field that is not in the PRD (PRD §5.3); record a change request first (PRD §25).

## Phase Map

| Phase | Scope | Exit Criteria |
| --- | --- | --- |
| 0 | Foundation (weeks 1-2): monorepo, CI, Docker Compose, Alembic, Supabase projects, staff login (F-012), tenancy + RLS + audit skeleton, platform admin F-013/F-014, staff F-015, design tokens, i18n, Sentry, deploy staging | Admin creates a clinic, owner logs in with an email magic link, adds a reception user; a second clinic's owner gets 404 on the first clinic's data; CI green |
| 1 | Patient + queue core (weeks 3-4): doctors & OPD (F-016), booking F-001, confirm F-002, live queue F-003, token numbering, Turnstile, Realtime publish | From a phone, book 2 tokens for the same doctor; numbers are 1 and 2; limit reached closes booking; concurrency test passes |
| 2 | Reception, doctor, TV (weeks 5-7): F-004, F-005, F-006, F-007, F-008, F-009, F-020, F-021, day close job | Online + walk-in tokens in one list; doctor presses NEXT and TV + patient phone change within 3 s; day close marks no-shows; with sharing ON the patient sees the doctor's advice on the token link, with sharing OFF they do not |
| 3 | Owner (weeks 8-9): F-010/D-001, F-011, R-001..R-004, D-002, pilot hardening, backups + restore test | Owner turns online booking off and the booking page closes; daily report numbers match the token list; restore test passes; pilot clinic live |
| 4 | AI and add-ons (weeks 10-12): AI tool layer, F-019 chat, F-018 brief, AI summary in F-008, wait-time prediction, F-017, D-003, CSV export, TV voice (Q-005) | Patient asks "mera number kab aayega" and gets the correct number of people ahead; brief generated at 21:00; every AI call appears in F-017; Gemini fallback works when OpenRouter key is disabled |

## Production MVP and the Infrastructure Ladder

Phase 0 and Phase 1 are a **production MVP**: the smallest thing real users can rely on. Do not build for scale that has not arrived. Start at step 1 and move up only when the stated trigger is true and measured.

| Step | Setup | Move up when |
| --- | --- | --- |
| 1 | Free tiers: one managed host, one managed database, free error tracking and uptime check | Free-tier limits are reached or the uptime check shows repeated failures |
| 2 | Paid small instances, automated backups, staging environment, secrets in a manager | Paying users exist, or an outage would cost money |
| 3 | Autoscaling or multiple instances, read replicas or caching, structured logs and alerts | p95 latency or CPU stays above the PRD §17 target for a week |
| 4 | Multi-region, queues and workers, formal on-call and DR drills | A written availability or compliance requirement the lower steps cannot meet |

Anything the PRD wants beyond the MVP goes in a later phase with its trigger written next to it.

## Task Size Rule

A task must be verifiable in one fast-tier cycle (`bash scripts/verify.sh`, seconds). If its acceptance criteria need more than 6 checks, or any check needs the slow tier to prove the basic behaviour, split the task before starting it. `python3 scripts/check_plan.py` flags oversized tasks, duplicates, tasks without acceptance criteria, and a tracker that disagrees with this plan.

---

## Phase 0 — Foundation (weeks 1-2): monorepo, CI, Docker Compose, Alembic, Supabase projects, staff login (F-012), tenancy + RLS + audit skeleton, platform admin F-013/F-014, staff F-015, design tokens, i18n, Sentry, deploy staging

Exit gate: Admin creates a clinic, owner logs in with an email magic link, adds a reception user; a second clinic's owner gets 404 on the first clinic's data; CI green

- [x] 00 Architecture Decision Record + sign-off — write `docs/adr/0001-stack-decision.md` from PRD §3.1 (stack, why, rejected alternatives)
  - Acceptance: `docs/adr/0001-stack-decision.md` exists and names the stack, the reasons and the rejected alternatives
  - Acceptance: The developer has signed it off (recorded in the progress log)
- [x] 01 Repo scaffold — folders per PRD §3.4 (`apps/api`, `apps/web`, `apps/api/app/ai`, `infra`, `packages/api-client`), package managers, `.env.example` with empty values
  - Acceptance: Every folder in PRD §3.4 exists and each part builds or runs an empty smoke test
  - Acceptance: `.env.example` lists every variable with an empty value; no real secret is committed
- [x] 02 CI/CD + verification — one workflow per lane (api, web, agents, infra, client) calling `scripts/verify.sh`; secret scan; dependency scan
  - Acceptance: Every lane has a workflow that calls `scripts/verify.sh`; a deliberately broken commit turns CI red
  - Acceptance: Secret scan and dependency scan run and pass on the clean tree
- [x] 03 Database foundation — PostgreSQL (Supabase) + Alembic; first migration; naming and key conventions from PRD §12.2; migration check in `verify.sh`
  - Acceptance: The first migration applies to an empty database and the migration check in `verify.sh` passes
  - Acceptance: Table, column and key names follow PRD §12.2
- [x] 04 Authentication & authorization — login/refresh/logout, roles and permission matrix from PRD §14.2, enforced in the API
  - Acceptance: Login, refresh and logout work; a wrong password and an expired token are rejected
  - Acceptance: A user without the role gets 403 on a protected endpoint (test per role in PRD §14.2)
- [x] 05 Tenancy enforcement — central scoping filter, deny-by-default, cross-tenant access tests (PRD §3.5)
  - Acceptance: A test proves tenant A cannot read or write tenant B's rows
  - Acceptance: A request with no tenant context returns zero rows (deny by default)
- [x] 06 Audit infrastructure — audit rows for the actions in PRD §14.1, sensitive-field masking, test that each audited action writes a row
  - Acceptance: Each audited action in PRD §14.1 writes exactly one audit row (one test per action)
  - Acceptance: Sensitive fields are masked in the stored row
- [x] 07 API conventions + contract — versioned base path, error format, OpenAPI, generated client (openapi), drift check in `verify.sh`
  - Acceptance: The generated client matches the live OpenAPI document; the drift check passes
  - Acceptance: Errors use the documented error format
- [x] 08 UI foundation — design tokens, layout shell, the mandated form layout (PRD §5.1), reusable grid/form/status components, `context/ui-registry.md` started
  - Acceptance: Design tokens are the only source of colour, type and spacing; a lint or grep check finds no hard-coded values
  - Acceptance: The layout shell renders at mobile and desktop widths without horizontal scroll
- [x] 09 Agent service skeleton — separate service, no database credentials, tool catalog wired to the API with the caller's identity (PRD §36.2-36.4)
  - Acceptance: The agent service has no database credentials in its environment
  - Acceptance: A tool call reaches the API with the caller's identity, and a forbidden call is rejected
- [ ] 10 Vertical slice — the smallest end-to-end feature across every layer, to prove the pattern later tasks copy
  - Acceptance: The smallest feature works end to end across every layer with one automated test
  - Acceptance: `scripts/verify.sh` passes and the pattern is written down for later tasks to copy
- [ ] 11 Staff Login — F-012 (Staff; transaction; P0; roles: all staff)
  - Acceptance: A user with one of the roles (all staff) can complete the Staff flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-012 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 12 New Clinic (onboarding) — F-013 (Platform; master; P0; roles: platform_admin)
  - Acceptance: A user with one of the roles (platform_admin) can complete the Platform flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-013 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 13 Clinics List — F-014 (Platform; list; P0; roles: platform_admin)
  - Acceptance: A user with one of the roles (platform_admin) can complete the Platform flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-014 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 14 Staff Management — F-015 (Owner; master; P0; roles: owner)
  - Acceptance: A user with one of the roles (owner) can complete the Owner flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-015 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 15 Integration: Supabase Auth (email magic link; custom SMTP: Gmail app password in dev, own-domain sender in prod per Q-007) — I-001 (out/in; HTTPS, JWT/JWKS)
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test
- [ ] 16 Integration: Sentry — I-006 (out; HTTPS)
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test
- [ ] 17 Scaffold the web app with the chosen framework, strict TypeScript, lint and format [web-app pack]
  - Acceptance: Fresh clone installs and builds
  - Acceptance: lint and typecheck run in the fast tier
- [x] 18 Design tokens and layout shell [web-app pack]
  - Acceptance: Tokens are the only source of colour, type and spacing
  - Acceptance: shell renders at 360 px and 1440 px without horizontal scroll
- [ ] 19 Authentication and role guard [web-app pack]
  - Acceptance: Login, logout and expiry work
  - Acceptance: a user without the role gets 403 on a protected route
- [ ] 20 Deploy a preview environment on a free tier [web-app pack]
  - Acceptance: Every pull request gets a preview URL
  - Acceptance: production deploy is one command
- [ ] 21 Scaffold the API with lint, format, typecheck and a health endpoint [backend-api pack]
  - Acceptance: The service starts from a clean clone
  - Acceptance: the health endpoint answers
- [x] 22 Database foundation and first migration [backend-api pack]
  - Acceptance: Migration applies to an empty database
  - Acceptance: the migration check passes in the fast tier
- [x] 23 Authentication and authorisation skeleton [backend-api pack]
  - Acceptance: Login works
  - Acceptance: a role without access gets 403
  - Acceptance: one test per role
- [x] 24 OpenAPI contract and generated client with a drift check [backend-api pack]
  - Acceptance: The drift check fails when an endpoint changes without regeneration
- [x] 25 Tool catalogue with schemas, permissions and a test per tool [agents pack]
  - Acceptance: A forbidden call is rejected
  - Acceptance: each tool has a unit test
- [ ] 26 Evaluation harness with a first golden set [agents pack]
  - Acceptance: The suite runs in the fast tier against recorded model responses
- [ ] 27 Vendor accounts, sandbox access and credentials in the secret manager [integrations pack]
  - Acceptance: A sandbox call succeeds from the dev environment
  - Acceptance: no credential is in the repository
- [ ] 28 Integration skill: install an upstream one or generate a project-local one [integrations pack]
  - Acceptance: The skill cites the vendor documentation URL and date

Each task: confirm the acceptance criteria (`/architect` turns them into failing tests first), then build, then `bash scripts/verify.sh`, then `/review`.

## Phase 1 — Patient + queue core (weeks 3-4): doctors & OPD (F-016), booking F-001, confirm F-002, live queue F-003, token numbering, Turnstile, Realtime publish

Exit gate: From a phone, book 2 tokens for the same doctor; numbers are 1 and 2; limit reached closes booking; concurrency test passes

- [ ] 29 Token Booking — F-001 (Patient; transaction; P0; roles: public)
  - Acceptance: A user with one of the roles (public) can complete the Patient flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-001 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 30 Token Confirm — F-002 (Patient; transaction; P0; roles: public)
  - Acceptance: A user with one of the roles (public) can complete the Patient flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-002 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 31 Live Queue — F-003 (Patient; list; P0; roles: public)
  - Acceptance: A user with one of the roles (public) can complete the Patient flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-003 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 32 Doctor Management — F-016 (Owner; master; P0; roles: owner)
  - Acceptance: A user with one of the roles (owner) can complete the Owner flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-016 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 33 Integration: Supabase Realtime broadcast — I-002 (out; HTTPS publish)
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test
- [ ] 34 Integration: Cloudflare Turnstile — I-003 (in; HTTPS verify)
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test
- [ ] 35 First vertical slice through the UI, API and database [web-app pack]
  - Acceptance: The slice works end to end with one automated test
  - Acceptance: the pattern is written down
- [ ] 36 Form pattern: validation, error display, double-submit protection [web-app pack]
  - Acceptance: Server and client reject the same invalid inputs
  - Acceptance: a second click does not create a second record
- [ ] 37 Accessibility and performance gates [web-app pack]
  - Acceptance: axe finds no serious issue on the slice
  - Acceptance: the performance budget lane passes
- [ ] 38 End-to-end smoke test of the critical flow [web-app pack]
  - Acceptance: One browser test signs in and completes the main task
- [ ] 39 First vertical slice: one resource with create, read, update, delete [backend-api pack]
  - Acceptance: Validation, authorisation and pagination are tested
  - Acceptance: error format matches the contract
- [ ] 40 Tenant or branch scoping (if the PRD has it) [backend-api pack]
  - Acceptance: A test proves tenant A cannot read or write tenant B
  - Acceptance: no tenant context returns nothing
- [ ] 41 Structured logging, request ids and error reporting [backend-api pack]
  - Acceptance: A failed request can be traced from the response id to the log line
- [ ] 42 Backups and one timed restore [backend-api pack]
  - Acceptance: The restore completes within the PRD recovery target
- [ ] 43 First agent flow end to end with human approval on side effects [agents pack]
  - Acceptance: An approved action runs
  - Acceptance: a rejected action does not
  - Acceptance: the trace shows both
- [ ] 44 Run caps, spend cap and kill switch [agents pack]
  - Acceptance: Exceeding a cap stops the run with a clear message
  - Acceptance: the kill switch works without a deploy
- [ ] 45 Tracing with redaction [agents pack]
  - Acceptance: A trace of a run contains no personal data from the test fixtures
- [ ] 46 Authentication to the vendor (OAuth or key) with token refresh [integrations pack]
  - Acceptance: Expired token refreshes without user action
  - Acceptance: revoked token produces a clear re-consent path
- [ ] 47 One end-to-end integration flow against the sandbox [integrations pack]
  - Acceptance: Contract test passes against a recorded response
  - Acceptance: timeout, 429 and error response each have a test
- [ ] 48 Webhook endpoint with signature verification and idempotency [integrations pack]
  - Acceptance: A replayed event is ignored
  - Acceptance: a bad signature is rejected
- [ ] 49 Failure handling and alerting [integrations pack]
  - Acceptance: A forced vendor outage shows the defined degraded behaviour and raises an alert

Each task: confirm the acceptance criteria (`/architect` turns them into failing tests first), then build, then `bash scripts/verify.sh`, then `/review`.

## Phase 2 — Reception, doctor, TV (weeks 5-7): F-004, F-005, F-006, F-007, F-008, F-009, F-020, F-021, day close job

Exit gate: Online + walk-in tokens in one list; doctor presses NEXT and TV + patient phone change within 3 s; day close marks no-shows; with sharing ON the patient sees the doctor's advice on the token link, with sharing OFF they do not

- [ ] 50 Aaj ki List — F-004 (Reception; list; P0; roles: reception, owner, doctor (own))
  - Acceptance: A user with one of the roles (reception, owner, doctor (own)) can complete the Reception flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-004 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 51 Walk-in Entry — F-005 (Reception; transaction; P0; roles: reception, owner)
  - Acceptance: A user with one of the roles (reception, owner) can complete the Reception flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-005 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 52 Patient Search & Profile — F-006 (Reception; list; P1; roles: reception, owner, doctor)
  - Acceptance: A user with one of the roles (reception, owner, doctor) can complete the Reception flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-006 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 53 Next Patient (Doctor Panel) — F-007 (Doctor; transaction; P0; roles: doctor)
  - Acceptance: A user with one of the roles (doctor) can complete the Doctor flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-007 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 54 Patient History & Visit Note — F-008 (Doctor; transaction; P1; roles: doctor)
  - Acceptance: A user with one of the roles (doctor) can complete the Doctor flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-008 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 55 TV Screen — F-009 (Waiting room; list; P0; roles: display device)
  - Acceptance: A user with one of the roles (display device) can complete the Waiting room flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-009 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 56 Display Device Pairing — F-020 (Owner; settings; P0; roles: owner)
  - Acceptance: A user with one of the roles (owner) can complete the Owner flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-020 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 57 Doctor ki Hidayat (shared visit advice) — F-021 (Patient; report; P1; roles: public (by code))
  - Acceptance: A user with one of the roles (public (by code)) can complete the Patient flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-021 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored

Each task: confirm the acceptance criteria (`/architect` turns them into failing tests first), then build, then `bash scripts/verify.sh`, then `/review`.

## Phase 3 — Owner (weeks 8-9): F-010/D-001, F-011, R-001..R-004, D-002, pilot hardening, backups + restore test

Exit gate: Owner turns online booking off and the booking page closes; daily report numbers match the token list; restore test passes; pilot clinic live

- [ ] 58 Roz ki Report — F-010 / dashboard D-001 (Owner; report; P1; roles: owner, doctor; KPIs: Patients seen, avg wait, no-shows, online vs walk-in, 7-day trend)
  - Acceptance: Each KPI (Patients seen, avg wait, no-shows, online vs walk-in, 7-day trend) matches a hand-computed value on a seeded dataset
  - Acceptance: Each KPI drills down to the F-004 list with the matching filter
  - Acceptance: Owner sees all doctors; a doctor sees only own numbers; reception gets 403
  - Acceptance: An empty day shows an empty state, not an error
- [ ] 59 Clinic Settings — F-011 (Owner; settings; P0; roles: owner)
  - Acceptance: A user with one of the roles (owner) can complete the Owner flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-011 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 61 Platform Overview dashboard — D-002 (role: platform_admin; KPIs: Active clinics, tokens today, tokens 7 days, clinics with zero activity 3+ days, AI spend this month)
  - Acceptance: Each KPI (Active clinics, tokens today, tokens 7 days, clinics with zero activity 3+ days, AI spend this month) matches a hand-computed value on a seeded dataset
  - Acceptance: Only role platform_admin can open it; an empty dataset shows an empty state, not an error

Each task: confirm the acceptance criteria (`/architect` turns them into failing tests first), then build, then `bash scripts/verify.sh`, then `/review`.

## Phase 4 — AI and add-ons (weeks 10-12): AI tool layer, F-019 chat, F-018 brief, AI summary in F-008, wait-time prediction, F-017, D-003, CSV export, TV voice (Q-005)

Exit gate: Patient asks "mera number kab aayega" and gets the correct number of people ahead; brief generated at 21:00; every AI call appears in F-017; Gemini fallback works when OpenRouter key is disabled

- [ ] 62 AI Activity Log — F-017 (AI; list; P1; roles: owner, platform_admin)
  - Acceptance: A user with one of the roles (owner, platform_admin) can complete the AI flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-017 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 63 Daily Brief — F-018 (AI; report; P2; roles: owner)
  - Acceptance: A user with one of the roles (owner) can complete the AI flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-018 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 64 Patient Chat Assistant — F-019 (AI; transaction; P2; roles: public)
  - Acceptance: A user with one of the roles (public) can complete the AI flow; a user without them gets 403
  - Acceptance: Validation and required fields match the field spec for F-019 in PRD §5.3 (one test per rule)
  - Acceptance: One end-to-end test drives the form and checks what was stored
- [ ] 65 AI Command Center dashboard — D-003 (role: owner, platform_admin; KPIs: AI calls, failures, fallback rate, cost, thumbs-down rate)
  - Acceptance: Each KPI (AI calls, failures, fallback rate, cost, thumbs-down rate) matches a hand-computed value on a seeded dataset
  - Acceptance: Only role owner, platform_admin can open it; an empty dataset shows an empty state, not an error
- [ ] 66 Integration: OpenRouter — I-004 (out; HTTPS (OpenAI-compatible))
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test
- [ ] 67 Integration: Google Gemini API — I-005 (out; HTTPS)
  - Acceptance: A contract test against a recorded or sandbox response proves the happy path
  - Acceptance: A timeout, an error response and a duplicate delivery are each handled by a test

Each task: confirm the acceptance criteria (`/architect` turns them into failing tests first), then build, then `bash scripts/verify.sh`, then `/review`.

## Pack Checklists — answer before Phase 1 exits

Each item becomes a PRD requirement and a candidate acceptance test. Tick it here when the PRD answers it.

- [ ] C-WA-01 Every protected page and every API route checks the user and role on the server, not only in the UI; one test per role proves a 403. (web-app)
- [ ] C-WA-02 Session expiry, refresh and logout are defined and tested, including what the user sees when a session ends mid-form. (web-app)
- [ ] C-WA-03 All input is validated on the client for feedback and again on the server for safety; the same rules are shared, not copied. (web-app)
- [ ] C-WA-04 Every list and screen has designed loading, empty and error states. (web-app)
- [ ] C-WA-05 Forms cannot be double-submitted; a repeated submit is safe. (web-app)
- [ ] C-WA-06 Keyboard-only use works on every page: logical focus order, visible focus, no keyboard traps; forms have labels and linked error messages. (web-app)
- [ ] C-WA-07 Layouts work at 360 px, tablet and desktop widths without horizontal scroll. (web-app)
- [ ] C-WA-08 Every page has a title, a description, one h1 and a canonical URL; public pages appear in the sitemap; private pages are noindex. (web-app)
- [ ] C-WA-09 Security headers and a content security policy are set; cookies are HttpOnly, Secure and SameSite; state-changing requests are protected against CSRF. (web-app)
- [ ] C-WA-10 Rate limiting protects sign-in, password reset and any public form. (web-app)
- [ ] C-WA-11 No secret reaches the browser bundle; environment files are separated per environment and `.env.example` lists every variable. (web-app)
- [ ] C-WA-12 Image, font and JavaScript budgets are written down as numbers and checked in a lane. (web-app)
- [ ] C-WA-13 Errors are captured with a request or session id and without personal data. (web-app)
- [ ] C-WA-14 404 and 500 pages exist and keep the navigation usable. (web-app)
- [ ] C-BA-01 Every endpoint validates input and rejects unknown or oversized fields with a consistent error format. (backend-api)
- [ ] C-BA-02 Authorisation is tested per endpoint and per role, including the case of a valid user reading another user's or tenant's data. (backend-api)
- [ ] C-BA-03 List endpoints are paginated with a hard maximum page size and a stable sort. (backend-api)
- [ ] C-BA-04 Requests that may be retried (payments, orders, imports) are idempotent or carry an idempotency key. (backend-api)
- [ ] C-BA-05 Migrations apply to an empty database and to a copy of production data, and each has a tested way back or a stated reason it has none. (backend-api)
- [ ] C-BA-06 Filtered and joined columns are indexed; the slowest queries are measured with realistic data volume. (backend-api)
- [ ] C-BA-07 Transaction boundaries are explicit; a failure half-way leaves no partial records. (backend-api)
- [ ] C-BA-08 Every outbound call has a timeout and a defined failure behaviour. (backend-api)
- [ ] C-BA-09 Health and readiness endpoints exist and reflect real dependencies. (backend-api)
- [ ] C-BA-10 Logs are structured, carry a request id, and never contain secrets or personal data. (backend-api)
- [ ] C-BA-11 CORS is an allowlist; secrets come from the environment or a secret manager, never the repository. (backend-api)
- [ ] C-BA-12 The OpenAPI document matches the running service; the generated client is checked for drift. (backend-api)
- [ ] C-BA-13 Rate limits protect authentication and expensive endpoints. (backend-api)
- [ ] C-BA-14 Personal data is identified, minimised, and has a stated retention and deletion rule. (backend-api)
- [ ] C-BA-15 A restore from backup has been performed once and timed. (backend-api)
- [ ] C-A-01 Every tool has the least privilege it needs, and a forbidden call is rejected, not merely discouraged in the prompt. (agents)
- [ ] C-A-02 The agent service has no database credentials; it reaches data only through the API with the caller's identity. (agents)
- [ ] C-A-03 Text returned by tools, web pages and documents is treated as untrusted and cannot change the agent's instructions or permissions. (agents)
- [ ] C-A-04 Each run has a maximum number of steps, tokens and wall-clock time, and ends with a clear message when a cap is hit. (agents)
- [ ] C-A-05 Destructive and customer-visible actions require explicit human approval until evaluations justify removing it. (agents)
- [ ] C-A-06 A golden-case evaluation suite runs in CI; a regression fails the build. (agents)
- [ ] C-A-07 Structured outputs are validated against a schema; invalid output is retried once and then escalated. (agents)
- [ ] C-A-08 Traces record prompts, tool calls and results with personal data redacted, and are kept for a stated period. (agents)
- [ ] C-A-09 Model errors, rate limits and timeouts have a defined fallback (retry, smaller model, human). (agents)
- [ ] C-A-10 Prompts and tool descriptions are versioned in the repository and changes go through review. (agents)
- [ ] C-A-11 A per-day spend cap exists with an alert and an automatic stop. (agents)
- [ ] C-A-12 A kill switch disables the agent without a deploy. (agents)
- [ ] C-A-13 Personal data sent to the model provider is identified and covered by the provider terms in use. (agents)
- [ ] C-I-01 A sandbox or recorded-fixture suite proves the happy path for every integration without touching production. (integrations)
- [ ] C-I-02 Tokens refresh automatically; revocation and re-consent are handled and tested. (integrations)
- [ ] C-I-03 Requested scopes are the minimum needed and each is justified in the PRD. (integrations)
- [ ] C-I-04 Incoming webhooks verify the signature, reject replays, and are idempotent. (integrations)
- [ ] C-I-05 Outgoing calls use timeouts, retries with backoff and jitter, and a dead-letter or failure record after the last retry. (integrations)
- [ ] C-I-06 Vendor rate limits are respected, and a 429 response is handled. (integrations)
- [ ] C-I-07 Vendor error codes are mapped to our error format; raw vendor errors never reach users. (integrations)
- [ ] C-I-08 The vendor is mocked in CI so builds do not depend on the vendor being up. (integrations)
- [ ] C-I-09 A data-mapping table lists each field, its source, its destination and any transformation. (integrations)
- [ ] C-I-10 Credentials are stored in a secret manager and have a rotation procedure. (integrations)
- [ ] C-I-11 The vendor API version is pinned and a change-notice source is subscribed to. (integrations)
- [ ] C-I-12 Failures are monitored and alert a human when the failure rate crosses the stated threshold. (integrations)
- [ ] C-I-13 The vendor's terms and data-processing obligations are read and any personal-data transfer is recorded. (integrations)

## Deferred — with the trigger that brings each back

| Item | Trigger | Pack |
| --- | --- | --- |
| CDN and caching tuning | p95 time to first byte is above the PRD target for a week | web-app |
| Internationalisation | A second language or market is committed | web-app |
| Feature flags and A/B testing | Two or more releases are blocked by the same unfinished feature, or a decision needs measured data | web-app |
| Offline or installable app (PWA) | Users must work without connectivity, as stated in the PRD | web-app |
| Background job queue | A task takes longer than a request should wait, or must retry independently of the request | backend-api |
| Caching layer (Redis or similar) | A measured query or endpoint exceeds its target after indexing | backend-api |
| Search engine | Database search cannot meet the PRD response target at real data volume | backend-api |
| Read replicas | Reads saturate the primary after caching | backend-api |
| Microservices split | Two teams cannot deploy independently because of the monolith | backend-api |
| Long-term memory | Users repeat context across sessions and a retrieval test shows it improves outcomes | agents |
| Multiple cooperating agents | A single agent fails the golden set because of context length or role conflict | agents |
| Fine-tuning | Prompting and retrieval cannot reach the target on the golden set | agents |
| Autonomous execution without approval | The golden set shows a stated success rate over a stated number of runs | agents |
| Bulk sync and backfill jobs | Initial data volume cannot be handled by the incremental path | integrations |
| Second vendor in the same category | A customer requires it; extract a vendor-neutral interface then, not before | integrations |
| Real-time sync instead of polling | Polling latency breaks a stated user need | integrations |

