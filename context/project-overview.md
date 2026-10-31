# Project Overview

> Generated from `docs/prd/PRD.md` (v0.2.2, profile `production`) by Honey's Spec Harness. This is a living document: edit it freely; the PRD stays the source for scope.

## About the Project

Small clinics still run on a paper register and parchi. Patients do not know when their turn will come, the waiting room is overcrowded, and the reception phone keeps ringing with "number kitna chal raha hai?". The Clinic Token & Queue SaaS replaces this with one web application that has five parts: patients take a token from a link at home and follow the live queue on their phone; reception sees the whole day in one list and adds walk-in patients to the same queue; the doctor calls the next patient with one tap and sees the patient's history; a TV in the waiting room shows the current number in large type; and the owner sees the day's numbers on a phone.

The product is a multi-clinic SaaS built to the **production** profile on free tiers: Next.js web app, FastAPI API that alone owns business logic and data, Supabase Postgres and Auth, and Supabase Realtime for live queue updates. Every row belongs to a clinic and is isolated by the API and by row-level security. Four AI features (patient chat assistant, owner daily brief, visit-notes summary, wait-time prediction) run through OpenRouter with Gemini as fallback, and AI only acts through approved, permission-checked tools.

Delivery is five phases over ~10-12 weeks by one developer: foundation and multi-tenancy, patient booking and live queue, reception/doctor/TV, owner reports and settings, then AI and add-ons. Clinic subscription billing is deliberately out of scope until one or two clinics are live.

## Product Objectives

- Let a patient book a token for a chosen doctor and day (today/tomorrow) from a shared link in under 60 seconds, without login or app install.
- Show every patient their token number and estimated time immediately after booking.
- Show a live queue (current token, own token, people ahead, estimated wait) that updates within 3 seconds of the doctor pressing NEXT.
- Put online and walk-in tokens into one ordered queue per doctor per day.
- Give reception one list of today's tokens with status, filters and search, replacing the paper register.
- Let the doctor call, skip or hold a patient with one tap and see the patient's visit history and notes.
- Show the current and next tokens on a waiting-room TV that needs no login after pairing.
- Give the owner a daily report (patients, average wait, no-shows, 7-day chart) on a phone.
- Let the owner change clinic rules (online booking on/off, daily limit, OPD timing, doctors) without a developer.
- Isolate every clinic's data so no user of one clinic can read or change another clinic's data.
- Provide the four AI features at autonomy level L1-L2 (explain/recommend) with every AI call audited.
- Run within free-tier limits for at least the first 2 clinics.

### 2.1 Success metrics
| Metric | Baseline | Target | How measured |
| --- | --- | --- | --- |
| Share of tokens booked online (pilot clinic) | 0 % | ≥ 30 % after 4 weeks | `tokens.source` counts in D-001 |
| Reception phone calls asking queue status | Not measured (Q to clinic) | −50 % reported by reception | Pilot interview at week 4 |
| Queue update latency (NEXT → patient phone/TV) | n/a | p95 ≤ 3 s | Synthetic test in Phase 2 |
| Booking completion time | n/a | median ≤ 60 s | Front-end timing event |
| Wait-time estimate error | n/a | median absolute error ≤ 10 min (Phase 4 AI: ≤ 7 min) | `tokens.estimated_at` vs `called_at` |
| Cross-clinic data leaks | n/a | 0 (tested) | Tenancy integration tests |

### 2.2 Out of scope
- Clinic subscription billing and payment collection from clinics (after 1-2 live clinics, via §25).
- Online consultation-fee payment by patients (add-on, P2).
- Native iOS/Android apps.
- WhatsApp chat assistant and WhatsApp/SMS reminders (P2, deferred, paid APIs).
- E-prescriptions, pharmacy, lab integration, billing/invoicing inside the clinic.
- Video consultation.
- Urdu script / RTL layout (strings are i18n-ready; Roman Urdu + English only in v1).

## Modules & Primary Screens

| Module | Screens | Tables | APIs |
| --- | --- | --- | --- |
| Platform | F-013, F-014, D-002 | clinics, platform_admins | `/admin/*` |
| Access | F-012, F-015 | clinic_members, audit_logs | `/me`, `/members` |
| Clinic setup | F-011, F-016, F-020 | clinic_settings, doctors, doctor_schedules, display_devices | `/settings`, `/doctors`, `/displays` |
| Patient booking | F-001, F-002, F-003 | patients, tokens, token_counters, token_events | `/public/*` |
| Reception | F-004, F-005, F-006 | tokens, patients | `/tokens`, `/patients` |
| Doctor | F-007, F-008 | tokens, visits, visit_attachments | `/queues`, `/visits` |
| Patient advice | F-021 | visits, clinic_settings | `/public/tokens/{code}/advice` |
| Waiting room | F-009 | display_devices, tokens | `/display/*` |
| Reports | F-010, D-001, R-001..R-005 | daily_stats | `/reports/*` |
| AI | F-017, F-018, F-019, D-003 | ai_runs, ai_briefs, chat_messages, wait_predictions | `/ai/*`, `/public/tokens/{code}/chat`, `/visits/{id}/ai-summary` |

## Feature Priority

| Priority | Meaning | Items |
| --- | --- | --- |
| P0 — Mandatory MVP | Cannot ship without | F-001, F-002, F-003, F-004, F-005, F-007, F-009, F-011, F-012, F-013, F-014, F-015, F-016, F-020; tenancy, audit, Realtime, day close |
| P1 — Commercial release | Needed before second clinic | F-006, F-008, F-021, F-010/D-001, D-002, R-001, R-003, R-004, F-017, wait-time prediction |
| P2 — Expansion | Add-ons from blueprint | F-018, F-019, CSV export R-002, attachments, browser reminders, token slip print, TV voice |
| P3 — Differentiation | Later | WhatsApp/SMS reminders, online payment, subscription billing, multi-branch, Urdu RTL, PDF reports |

## Non-Negotiable Architectural Constraints

1. The API is the only component that reads or writes the database. The browser uses the Supabase client only for Auth sessions and Realtime subscriptions.
2. Every tenant table has `clinic_id`, every query is scoped, and a test proves cross-clinic access returns 404.
3. Business rules live in `services/`; routers and AI tools call services and contain no rules.
4. The AI layer holds no database credentials and runs no SQL; it calls tools that call services with the requesting user's identity and permissions.
5. Realtime payloads contain token numbers and counts only — never patient names or phones.
6. Token numbers are generated inside one database transaction with a row lock; the same number is never issued twice for one doctor and day.
7. Every schema change ships as an Alembic migration in the same PR.
8. Every state change on a token writes a `token_events` row and an audit entry.

## Deployment Models

| Env | Web | API | Database |
| --- | --- | --- | --- |
| Local | `next dev` | `uvicorn` | Docker Compose Postgres 16 + Supabase CLI (auth/realtime) |
| CI | build + test | pytest against Postgres service container | ephemeral |
| Staging | Vercel preview | Cloud Run `api-staging` | Supabase project `staging` |
| Production | Vercel production | Cloud Run `api-prod` | Supabase project `prod` |

Auth email delivery per environment:

| Env | Supabase Auth email sender | Status |
| --- | --- | --- |
| Development (hosted Supabase project) | Custom SMTP, Gmail account with an app password | Working; confirmation email delivered and link signed in on 2026-10-20 |
| Staging / Production | Custom SMTP, Gmail app password (a separate app password per environment) | Owner decision 2026-10-31; own-domain sender deferred (§3.2) |

The built-in Supabase sender (about 2 emails per hour per project) is not used in any environment. The Gmail app password is entered only in the Supabase dashboard SMTP settings and is never stored in the repository or `.env` files.

Config via environment variables only; `.env.example` lists every key with empty values. Secrets live in Vercel/Cloud Run secret settings and GitHub Actions secrets.

## Definition of Done

- Requirement implemented and demonstrated
- Database migration included
- API and UI completed
- Validation and authorization implemented
- Audit requirements implemented
- Automated tests added and passing; `scripts/verify.sh` passes
- No critical/high unresolved defects
- Code reviewed by a human developer (including AI-generated code)
- Documentation updated
- UAT passed

