# Progress Tracker

Update this file after every completed task. Anyone reading it should immediately know what is done, what is in progress, and what is next.

---

## Current Status

**Phase:** Phase 0 — Foundation (weeks 1-2): monorepo, CI, Docker Compose, Alembic, Supabase projects, staff login (F-012), tenancy + RLS + audit skeleton, platform admin F-013/F-014, staff F-015, design tokens, i18n, Sentry, deploy staging
**Last completed:** 13 Clinics List
**In progress:** 14 Staff Management
**Next:** 15 Integration: Supabase Auth
**Blockers:** None

---

## Phase 0 — Foundation (weeks 1-2): monorepo, CI, Docker Compose, Alembic, Supabase projects, staff login (F-012), tenancy + RLS + audit skeleton, platform admin F-013/F-014, staff F-015, design tokens, i18n, Sentry, deploy staging

- [x] 00 Architecture Decision Record + sign-off
- [x] 01 Repo scaffold
- [x] 02 CI/CD + verification
- [x] 03 Database foundation
- [x] 04 Authentication & authorization
- [x] 05 Tenancy enforcement
- [x] 06 Audit infrastructure
- [x] 07 API conventions + contract
- [x] 08 UI foundation
- [x] 09 Agent service skeleton
- [x] 10 Vertical slice
- [x] 11 Staff Login
- [x] 12 New Clinic (onboarding)
- [x] 13 Clinics List
- [ ] 14 Staff Management
- [ ] 15 Integration: Supabase Auth (email magic link; custom SMTP: Gmail a…
- [ ] 16 Integration: Sentry
- [ ] 17 Scaffold the web app with the chosen framework, strict TypeScript,…
- [x] 18 Design tokens and layout shell [web-app pack]
- [ ] 19 Authentication and role guard [web-app pack]
- [ ] 20 Deploy a preview environment on a free tier [web-app pack]
- [ ] 21 Scaffold the API with lint, format, typecheck and a health endpoin…
- [x] 22 Database foundation and first migration [backend-api pack]
- [x] 23 Authentication and authorisation skeleton [backend-api pack]
- [x] 24 OpenAPI contract and generated client with a drift check [backend-…
- [x] 25 Tool catalogue with schemas, permissions and a test per tool [agen…
- [ ] 26 Evaluation harness with a first golden set [agents pack]
- [ ] 27 Vendor accounts, sandbox access and credentials in the secret mana…
- [ ] 28 Integration skill: install an upstream one or generate a project-l…

## Phase 1 — Patient + queue core (weeks 3-4): doctors & OPD (F-016), booking F-001, confirm F-002, live queue F-003, token numbering, Turnstile, Realtime publish

- [ ] 29 Token Booking
- [ ] 30 Token Confirm
- [ ] 31 Live Queue
- [ ] 32 Doctor Management
- [ ] 33 Integration: Supabase Realtime broadcast
- [ ] 34 Integration: Cloudflare Turnstile
- [ ] 35 First vertical slice through the UI, API and database [web-app pac…
- [ ] 36 Form pattern: validation, error display, double-submit protection…
- [ ] 37 Accessibility and performance gates [web-app pack]
- [ ] 38 End-to-end smoke test of the critical flow [web-app pack]
- [ ] 39 First vertical slice: one resource with create, read, update, dele…
- [ ] 40 Tenant or branch scoping (if the PRD has it) [backend-api pack]
- [ ] 41 Structured logging, request ids and error reporting [backend-api p…
- [ ] 42 Backups and one timed restore [backend-api pack]
- [ ] 43 First agent flow end to end with human approval on side effects [a…
- [ ] 44 Run caps, spend cap and kill switch [agents pack]
- [ ] 45 Tracing with redaction [agents pack]
- [ ] 46 Authentication to the vendor (OAuth or key) with token refresh [in…
- [ ] 47 One end-to-end integration flow against the sandbox [integrations…
- [ ] 48 Webhook endpoint with signature verification and idempotency [inte…
- [ ] 49 Failure handling and alerting [integrations pack]

## Phase 2 — Reception, doctor, TV (weeks 5-7): F-004, F-005, F-006, F-007, F-008, F-009, F-020, F-021, day close job

- [ ] 50 Aaj ki List
- [ ] 51 Walk-in Entry
- [ ] 52 Patient Search & Profile
- [ ] 53 Next Patient (Doctor Panel)
- [ ] 54 Patient History & Visit Note
- [ ] 55 TV Screen
- [ ] 56 Display Device Pairing
- [ ] 57 Doctor ki Hidayat (shared visit advice)

## Phase 3 — Owner (weeks 8-9): F-010/D-001, F-011, R-001..R-004, D-002, pilot hardening, backups + restore test

- [ ] 58 Roz ki Report (F-010 / D-001)
- [ ] 59 Clinic Settings
- [ ] 61 Platform Overview dashboard

## Phase 4 — AI and add-ons (weeks 10-12): AI tool layer, F-019 chat, F-018 brief, AI summary in F-008, wait-time prediction, F-017, D-003, CSV export, TV voice (Q-005)

- [ ] 62 AI Activity Log
- [ ] 63 Daily Brief
- [ ] 64 Patient Chat Assistant
- [ ] 65 AI Command Center dashboard
- [ ] 66 Integration: OpenRouter
- [ ] 67 Integration: Google Gemini API


## History

Finished work, decisions and rulings are appended to `context/progress-log.md` (append-only). Keep this file short: update the status block and tick the checklist, nothing else.

## Open Questions

_From PRD §0.4. Resolve or escalate before the task that depends on it._

- Q-003 Is token slip printing (screen 5, optional) needed at pilot? Which printer (thermal 58/80 mm)? (blocks F-005, Phase 2)
- Q-004 Consent text shown when the owner turns `ai_notes_enabled` ON still has to be written (decision itself: clinic on/off, default off). (blocks §36, Phase 4)
- Q-008 Should a patient see shared advice for older visits, or only the visit linked to the current token link? (Draft: current visit only, visible 30 days.) (blocks F-021, Phase 2)
- Q-005 TV announcement with voice (screen 9, optional): browser text-to-speech in Urdu/English acceptable? (blocks F-009, Phase 4)
- Q-006 Who signs off the PRD and each phase gate? (blocks §28)
