---
project: "Clinic Token & Queue SaaS"
slug: "clinic-token-queue"
version: "0.2.2"
status: draft
profile: production
date: "2026-10-31"
owners: ["Product owner (to confirm)"]
stack:
  frontend: "Next.js (App Router, TypeScript strict) + Tailwind CSS v4 + shadcn/ui"
  backend: "FastAPI (Pydantic v2) + SQLAlchemy 2"
  database: "PostgreSQL (Supabase)"
  migrations: "Alembic"
  api_contract: "openapi"
  agents: "OpenAI-compatible function calling via OpenRouter, Google Gemini fallback"
  infra: "Docker Compose (local), GitHub Actions, Vercel (web), Google Cloud Run (api)"
features:
  - tenancy
  - audit
  - ui
  - ai-agents
  - api-contract
  - database
  - compliance
layout:
  api: apps/api
  web: apps/web
  agents: apps/api/app/ai
  infra: infra
  client: packages/api-client
phases: 5
packs: [web-app, backend-api, agents, integrations]
---

# Clinic Token & Queue SaaS — Product Requirements & Technical Specification

## 0. Document Control

### 0.1 Purpose and audience
This document is the single source of truth for the scope of the Clinic Token & Queue SaaS. It is written for the developer (and any AI coding agent working with them), the product owner, QA and pilot clinics. It was produced from the "Clinic App Blueprint — 12 Screens" (16 screenshots in `context-images/`, summarised in `APP_OVERVIEW.md`) and a discovery interview (`docs/prd/discovery-log.md`). Any change to scope goes through §25.

### 0.2 Revision history
| Version | Date | Author | Summary of change | Sections touched |
| --- | --- | --- | --- | --- |
| 0.1.0 | 2026-10-31 | Claude (prd skill) | Initial draft from blueprint images and discovery interview | all |
| 0.2.0 | 2026-10-31 | Claude (prd skill) | Pakistan-only clinics (Q-001); staff login by email magic link (Q-002); clinic on/off settings for sharing visit advice with patients (new F-021, W-011) and for AI use of notes (Q-004) | 0.3, 0.4, 3.1, 3.2, 4, 5.2, 5.3, 10, 12.3, 13, 14, 22, 26, 27, 30, 34, 35, 36, App. A-C |
| 0.2.1 | 2026-10-31 | Claude (prd skill) | Recorded the working development email setup (custom SMTP via Gmail app password, verified 2026-10-20); production sender still open | 0.4, 3.6, 13.3, 14, App. A-C |
| 0.2.2 | 2026-10-31 | Claude (prd skill) | Owner decision: keep custom SMTP via Gmail app password; Q-007 closed; own-domain sender moved to §3.2 with a trigger | 0.4, 3.2, 3.6, App. A-B |

### 0.3 Assumptions ledger
| ID | Assumption | Basis | Owner to confirm |
| --- | --- | --- | --- |
| A-001 | A **Platform Admin** (super-admin) role exists to onboard and activate/deactivate clinics. It is not in the blueprint. | Multi-clinic SaaS answer; billing is manual for now | Product owner |
| A-002 | Patients never log in and never install an app. They track a token through an unguessable link (`/t/{public_code}`). | Blueprint screen 1: "phone pe, app install nahi" | Product owner |
| A-003 | Patients are not OTP-verified at booking (SMS costs money). Abuse is limited by rate limits, one active token per phone per doctor per day, and a free CAPTCHA (Cloudflare Turnstile). | Free-tier budget | Product owner |
| A-004 | Estimated time = average consult minutes of that doctor (rolling last 20 visits, default from settings) × people ahead + OPD start offset. AI prediction (Phase 4) replaces it only when it is measurably better. | Blueprint screens 2-3 | Developer |
| A-005 | Live updates are pushed with Supabase Realtime **broadcast** channels published only by the API. Browsers never read queue tables directly. Fallback: 15 s polling. | Realtime need + "API owns data" rule | Developer |
| A-006 | One phone number can own several patient profiles (e.g. "Mareez A (bachcha)"). | Blueprint screen 6 | Product owner |
| A-007 | The patient chat assistant is a web widget on the token page. WhatsApp chat is deferred (paid API). | Free-tier budget | Product owner |
| A-008 | Agent framework: plain OpenAI-compatible function calling through the `openai` Python SDK pointed at OpenRouter; Gemini via `google-genai` as fallback. No separate agent service: AI code lives in `apps/api/app/ai` but calls domain services through a tool layer with the caller's permissions, never raw SQL. | One developer, free tier, "AI is a client" rule | Developer |
| A-009 | Time zone is `Asia/Karachi` for all clinics (field kept per clinic for future); a "day" for tokens is the clinic's local calendar day; phone numbers default to +92 and are stored in E.164. | Owner: clinics are in Pakistan (Q-001) | Product owner |
| A-010 | Web (Next.js) is hosted on Vercel and the API on Google Cloud Run free tier. Vercel Hobby forbids commercial use, so the web host moves to Vercel Pro or Cloudflare when the first clinic pays. | Free-tier budget | Product owner |
| A-011 | A doctor can belong to one clinic only in v1. | Simplicity | Product owner |
| A-013 | Only the **advice / dawa** part of a visit is shared with the patient. The doctor's `notes` field stays private to the clinic even when sharing is on. | Owner: clinic decides whether patients get notes; private clinical notes need a separate place | Product owner |
| A-014 | When sharing is on, the doctor still gets a per-visit "Mareez ko dikhayein" checkbox (default ticked) so a sensitive visit can be kept private. | Owner: "it depends on them" | Product owner |
| A-015 | AI use of visit notes follows the same pattern: clinic setting `ai_notes_enabled`, default OFF. | Owner's on/off answer applied to Q-004 | Product owner |
| A-012 | Unfinished tokens at day close become `no_show` (never arrived) or `done` is not inferred; `serving` at close becomes `done`. | Report needs "aaye nahi" | Product owner |

### 0.4 Open questions
| ID | Question | Blocks (section/phase) | Owner | Status |
| --- | --- | --- | --- | --- |
| Q-001 | Which country will clinics be in? → **Pakistan.** | §14.3, §34, Phase 1 | Product owner | closed 2026-10-31 |
| Q-002 | Staff login method? → **Email magic link** (Supabase Auth, free). | F-012, Phase 0 | Product owner | closed 2026-10-31 |
| Q-003 | Is token slip printing (screen 5, optional) needed at pilot? Which printer (thermal 58/80 mm)? | F-005, Phase 2 | Pilot clinic | open |
| Q-004 | May visit notes be sent to OpenRouter/Gemini? → **Clinic decides with an on/off setting** (`ai_notes_enabled`, default off). Consent wording for the setting still to be written. | §36, Phase 4 | Product owner | closed 2026-10-31 |
| Q-007 | Which email sender does Supabase Auth use? → **Owner decision: custom SMTP with a Gmail app password** (working since 2026-10-20). An own-domain sender is deferred (§3.2). | F-012 | Developer | closed 2026-10-31 |
| Q-008 | Should a patient see shared advice for older visits, or only the visit linked to the current token link? (Draft: current visit only, visible 30 days.) | F-021, Phase 2 | Product owner | open |
| Q-005 | TV announcement with voice (screen 9, optional): browser text-to-speech in Urdu/English acceptable? | F-009, Phase 4 | Pilot clinic | open |
| Q-006 | Who signs off the PRD and each phase gate? | §28 | Product owner | open |

### 0.5 Glossary
| Term | Meaning in this product |
| --- | --- |
| Mareez | Patient |
| Malik | Clinic owner (role `owner`) |
| Parchi | Paper slip / register entry the product replaces |
| Token | A numbered place in one doctor's queue for one day |
| OPD | Out-patient department; here, a doctor's daily sitting with a timing |
| Walk-in | Patient who arrives without booking online; reception creates the token |
| Queue | Ordered tokens of one doctor for one clinic day |
| Baari | A patient's turn |
| No-show ("aaye nahi") | Token whose patient never arrived before day close |
| Clinic (tenant) | One customer of the SaaS; all its data is isolated |
| Public code | Random, unguessable string in a patient's token link |
| Display device | A TV/monitor paired to one clinic to show the queue |

---

## 1. Executive Summary
Small clinics still run on a paper register and parchi. Patients do not know when their turn will come, the waiting room is overcrowded, and the reception phone keeps ringing with "number kitna chal raha hai?". The Clinic Token & Queue SaaS replaces this with one web application that has five parts: patients take a token from a link at home and follow the live queue on their phone; reception sees the whole day in one list and adds walk-in patients to the same queue; the doctor calls the next patient with one tap and sees the patient's history; a TV in the waiting room shows the current number in large type; and the owner sees the day's numbers on a phone.

The product is a multi-clinic SaaS built to the **production** profile on free tiers: Next.js web app, FastAPI API that alone owns business logic and data, Supabase Postgres and Auth, and Supabase Realtime for live queue updates. Every row belongs to a clinic and is isolated by the API and by row-level security. Four AI features (patient chat assistant, owner daily brief, visit-notes summary, wait-time prediction) run through OpenRouter with Gemini as fallback, and AI only acts through approved, permission-checked tools.

Delivery is five phases over ~10-12 weeks by one developer: foundation and multi-tenancy, patient booking and live queue, reception/doctor/TV, owner reports and settings, then AI and add-ons. Clinic subscription billing is deliberately out of scope until one or two clinics are live.

## 2. Product Objectives
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

## 3. Technology & Architecture

### 3.1 Stack decision record
| Layer | Required technology / standard | Why this choice | Considered and rejected |
| --- | --- | --- | --- |
| UI | Next.js App Router, TypeScript strict, Tailwind CSS v4, shadcn/ui, React Hook Form + Zod, TanStack Query, Recharts | Owner's choice; server-rendered public pages are fast on cheap phones | React+Vite SPA (worse first load on patient phones) |
| Backend | FastAPI + Pydantic v2, Python 3.12, `uv`, ruff, mypy | Owner's choice; good fit for AI work | Next.js route handlers only (business logic would leak into UI) |
| Business logic | Domain service layer in `apps/api/app/services`, called by routers and AI tools alike | One place for rules; AI uses the same rules | Logic in routers |
| ORM / data access | SQLAlchemy 2 (async, asyncpg) | Mature, typed | Supabase JS client from browser (bypasses API) |
| Database | PostgreSQL on Supabase (free tier) | Owner's choice; free; RLS available | MongoDB (relational data) |
| Migrations | Alembic, one migration per schema change, CI drift check | Production profile requirement | Supabase dashboard edits |
| API | REST + OpenAPI 3.1 at `/api/v1`; generated TS client in `packages/api-client` | Contract drift is checked in CI | GraphQL, tRPC |
| Authentication | Supabase Auth: staff via **email magic link**; API verifies Supabase JWT (JWKS). Patients never log in. | Managed, free, no SMS cost | Phone OTP (SMS costs money); own auth code |
| Authorization | Role → permission matrix in API (`platform_admin`, `owner`, `doctor`, `reception`); RLS as a second guard | Server-side enforcement | UI-only checks |
| Background jobs | Postgres-backed scheduled jobs via Cloud Scheduler → authenticated API endpoints (day close, daily brief, estimate refresh) | No extra infra on free tier | Celery + Redis |
| Cache / queue | None in v1 (Postgres row locks for token counters) | Load is small | Redis (deferred, §3.2) |
| Search | Postgres `pg_trgm` index on patient name and phone | Enough for per-clinic search | Meilisearch |
| File storage | Supabase Storage, private buckets per clinic (visit attachments, P2) | Free tier, signed URLs | S3 |
| Realtime | Supabase Realtime broadcast, channel per clinic+doctor, published by API only; 15 s polling fallback | Free, no own WebSocket server | FastAPI WebSockets (Cloud Run scale-to-zero breaks long connections) |
| AI / agents | OpenRouter (OpenAI-compatible) primary, Google Gemini fallback, tool layer in API | Owner's choice | Direct DB access by AI (forbidden) |
| Observability | Sentry free tier (web + api), structured JSON logs with `request_id` | Production profile | Self-hosted Grafana (too much for 1 dev) |
| CI/CD | GitHub Actions: lint, typecheck, tests (Postgres service), Alembic drift, OpenAPI client drift | Free for public/private small use | — |
| Hosting / deployment | Web: Vercel; API: Google Cloud Run (free tier); DB/Auth/Realtime/Storage: Supabase | Free tiers | Render free (sleeps, slow cold start) |
| Containers | Docker for API image; Docker Compose for local Postgres | Local/CI parity | Kubernetes |
| Testing | pytest + httpx (API), Vitest + Testing Library (web), Playwright (E2E), axe | Standard | — |

### 3.2 Considered and deferred
| Technology | Why not now | Trigger to adopt |
| --- | --- | --- |
| Redis / Valkey | Postgres locks and Supabase Realtime cover current load | > 300 concurrent live-queue viewers per clinic or p95 API > 300 ms on queue reads for a week |
| Dedicated worker queue (arq/Celery) | Few scheduled jobs; Cloud Scheduler is enough | AI or report jobs exceed 30 s or need retries at scale |
| WhatsApp Business API | Paid per conversation | First clinic agrees to pay for reminders |
| Own-domain email sender (e.g. Resend/Brevo with SPF/DKIM) | Owner decided Gmail SMTP is enough for now | Gmail daily cap reached, login emails land in spam, or a clinic needs branded email |
| SMS reminders / SMS OTP (local Pakistani gateway) | Paid | A clinic agrees to pay for reminders, or staff ask for phone login |
| Subscription billing (Stripe/local gateway) | Owner decision: after 1-2 live clinics | Second clinic signs |
| Urdu script / RTL | Not needed for pilot | A clinic requests it |
| Separate AI service | One developer; tool layer gives the same isolation rule | AI load or deploy cadence differs from API |
| pgvector / RAG | No document corpus yet | Chat assistant needs clinic FAQ beyond settings fields |
| Kubernetes / microservices | Not justified | Never at this size |

### 3.3 Architecture overview
```
Patient phone (no login) ─┐
Reception / Doctor / Owner ├─► Next.js web (Vercel) ──HTTPS──► FastAPI /api/v1 (Cloud Run)
TV display (paired)  ─────┘                                      │  routers → services → SQLAlchemy
                                                                 │  ai/ tools → services (same permissions)
                                                                 ├──► Supabase Postgres (sole data owner: API)
                                                                 ├──► Supabase Auth (JWT verify via JWKS)
                                                                 ├──► Supabase Realtime broadcast (publish only)
                                                                 └──► OpenRouter / Gemini (AI, no DB creds)
Browsers subscribe to Realtime channel `queue:{clinic_id}:{doctor_id}` (payload has numbers only, no PII).
Cloud Scheduler ──► POST /api/v1/jobs/{day-close|daily-brief|estimates} (service token)
```

### 3.4 Repository layout
```
clinic-token-queue/
├─ apps/
│  ├─ web/                 # Next.js: (public)/c/[slug], (public)/t/[code], (staff)/..., (display)/tv
│  └─ api/
│     ├─ app/
│     │  ├─ routers/       # HTTP only
│     │  ├─ services/      # business rules (tokens, queue, patients, reports, settings)
│     │  ├─ models/        # SQLAlchemy
│     │  ├─ schemas/       # Pydantic
│     │  ├─ ai/            # tool layer, prompts, providers (openrouter, gemini)
│     │  └─ core/          # auth, tenancy scope, audit, realtime publisher, errors
│     ├─ alembic/
│     └─ tests/
├─ packages/
│  └─ api-client/          # generated from OpenAPI
├─ infra/                  # docker-compose.yml, Dockerfile, GitHub Actions, Cloud Run config
└─ docs/prd/               # this PRD, discovery log
```

### 3.5 Multi-tenancy and scoping
- Every business table carries `clinic_id uuid not null` (FK `clinics.id`) and a composite index starting with `clinic_id`.
- The API resolves the caller's `clinic_id` from `clinic_members` (staff) or from the public slug/public code (patients, display devices); it is never taken from the request body.
- A single `ScopedSession` dependency adds `clinic_id` filters to every query; an architecture test fails if a service queries a tenant table without the scope.
- Postgres RLS is enabled on every tenant table as a second guard (policies on `app.clinic_id` session setting set by the API per transaction).
- Only `platform_admin` may act across clinics, through `/api/v1/admin/*` endpoints, and every such action is audited.

### 3.6 Environments and deployment models
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

### 3.7 Architectural constraints (non-negotiable)
1. The API is the only component that reads or writes the database. The browser uses the Supabase client only for Auth sessions and Realtime subscriptions.
2. Every tenant table has `clinic_id`, every query is scoped, and a test proves cross-clinic access returns 404.
3. Business rules live in `services/`; routers and AI tools call services and contain no rules.
4. The AI layer holds no database credentials and runs no SQL; it calls tools that call services with the requesting user's identity and permissions.
5. Realtime payloads contain token numbers and counts only — never patient names or phones.
6. Token numbers are generated inside one database transaction with a row lock; the same number is never issued twice for one doctor and day.
7. Every schema change ships as an Alembic migration in the same PR.
8. Every state change on a token writes a `token_events` row and an audit entry.

## 4. Application Navigation / Main Menu
- **Public (no login)**
  - `/c/{clinic-slug}` → F-001 Token Booking
  - `/t/{public-code}` → F-002 Token Confirm → F-003 Live Queue (+ F-019 Chat Assistant)
- **Display (paired device)**: `/tv` → F-009 TV Screen
- **Staff (login F-012)** — items the role lacks are hidden; the API still enforces.
  - Reception: Aaj ki List (F-004) · Walk-in Entry (F-005) · Patient Search (F-006)
  - Doctor: Next Patient (F-007) · Patient History (F-008) · Aaj ki List (read-only filter to self)
- **Public, after the visit**: `/t/{public-code}` also shows F-021 Doctor ki Hidayat when the clinic allows sharing
  - Owner: Roz ki Report (F-010/D-001) · Daily Brief (F-018) · Settings (F-011) · Doctors (F-016) · Staff (F-015) · Display Devices (F-020) · AI Activity (F-017) · all reception screens
  - Platform Admin: Clinics (F-014) · New Clinic (F-013) · Platform Overview (D-002) · AI Activity (F-017, all clinics)

## 5. Form & Screen Specification

### 5.1 Mandated form layout
Mobile-first. Every staff screen: **Header** (clinic name, screen title, date, live status dot) → **Filters/master fields** → **Content** (list, card or grid) → **Primary action** (bottom on mobile, right on desktop) → **Status/audit line** (last updated, by whom). Public screens: clinic logo/name → one task per screen → one primary button. TV screen: full-screen, no controls.

### 5.2 Form register
| ID | Form / screen | Module | Type (master, transaction, list, settings, report) | Roles | Priority | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| F-001 | Token Booking | Patient | transaction | public | P0 | 1 |
| F-002 | Token Confirm | Patient | transaction | public | P0 | 1 |
| F-003 | Live Queue | Patient | list | public | P0 | 1 |
| F-004 | Aaj ki List | Reception | list | reception, owner, doctor (own) | P0 | 2 |
| F-005 | Walk-in Entry | Reception | transaction | reception, owner | P0 | 2 |
| F-006 | Patient Search & Profile | Reception | list | reception, owner, doctor | P1 | 2 |
| F-007 | Next Patient (Doctor Panel) | Doctor | transaction | doctor | P0 | 2 |
| F-008 | Patient History & Visit Note | Doctor | transaction | doctor | P1 | 2 |
| F-009 | TV Screen | Waiting room | list | display device | P0 | 2 |
| F-010 | Roz ki Report | Owner | report | owner, doctor | P1 | 3 |
| F-011 | Clinic Settings | Owner | settings | owner | P0 | 3 |
| F-012 | Staff Login | Staff | transaction | all staff | P0 | 0 |
| F-013 | New Clinic (onboarding) | Platform | master | platform_admin | P0 | 0 |
| F-014 | Clinics List | Platform | list | platform_admin | P0 | 0 |
| F-015 | Staff Management | Owner | master | owner | P0 | 0 |
| F-016 | Doctor Management | Owner | master | owner | P0 | 1 |
| F-017 | AI Activity Log | AI | list | owner, platform_admin | P1 | 4 |
| F-018 | Daily Brief | AI | report | owner | P2 | 4 |
| F-019 | Patient Chat Assistant | AI | transaction | public | P2 | 4 |
| F-020 | Display Device Pairing | Owner | settings | owner | P0 | 2 |
| F-021 | Doctor ki Hidayat (shared visit advice) | Patient | report | public (by code) | P1 | 2 |

### 5.3 Field-level specifications

#### F-001 Token Booking
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| doctor_id | select (uuid) | yes | Active doctor of this clinic with OPD on chosen day | Label "Doctor / OPD" |
| visit_date | radio (date) | yes | `today` or `tomorrow` in clinic time zone; disabled if day full, closed or online booking off | "Aaj / Kal" |
| patient_name | text | yes | 2-60 chars, letters/spaces/.-' | |
| phone | tel | yes | E.164 after normalising local format (default country from clinic) | |
| turnstile_token | hidden | yes | Valid Cloudflare Turnstile response | Anti-abuse |
| Booking closed banner | read-only | — | Shown when limit reached or `online_booking_enabled=false` | "Booking band hai" |
| Share buttons | action | no | Copy link, WhatsApp share URL | Optional per blueprint |

#### F-002 Token Confirm
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| token_number | read-only int | — | From API | Large "#18" |
| doctor_name | read-only | — | | |
| estimated_time | read-only time | — | Per A-004; shown as "Andaazan time" | |
| live_queue_link | action | — | Opens F-003 | |
| cancel_token | action | no | Allowed only while status `booked`; confirm dialog | Optional |
| add_to_home | action | no | PWA bookmark hint | |

#### F-003 Live Queue
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| current_token | read-only int | — | From realtime/poll | "Abhi chal raha" |
| my_token | read-only int | — | | |
| people_ahead | read-only int | — | Count of `booked|arrived` tokens with lower position, excluding `hold` | |
| estimated_wait_minutes | read-only int | — | Recomputed on every queue event | |
| last_updated | read-only datetime | — | Shows "updated X s ago"; banner if > 60 s stale | |
| reminder_toggle | switch | no | Browser notification when `people_ahead ≤ 3` (P2) | |

#### F-004 Aaj ki List
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| date | date | yes | Default today; past dates read-only | |
| doctor_filter | select | no | Doctors of clinic | |
| status_filter | multi-select | no | booked, arrived, serving, done, skipped, hold, no_show, cancelled | |
| search | text | no | Name or phone, ≥ 2 chars | |
| Row: token_number, patient_name, phone (masked except last 4), source, status badge | read-only | — | | |
| Row action: mark_arrived | action | — | Only from `booked` | |
| Row action: cancel | action | — | Reason required | |

#### F-005 Walk-in Entry
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| patient_name | text | yes | 2-60 chars | Autocomplete from existing patients by phone |
| phone | tel | yes | E.164 | |
| doctor_id | select | yes | Active doctor with OPD today | |
| existing_patient_id | hidden uuid | no | Set when picked from autocomplete | |
| ignore_daily_limit | checkbox | no | Owner/reception may exceed online limit for walk-ins; audited | |
| Result: token_number | read-only | — | Shown large with "Print" (P2) | |

#### F-006 Patient Search & Profile
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| query | text | yes | ≥ 2 chars; trigram search on name, prefix on phone | |
| Result: name, visit_count, last_visit_date | read-only | — | | |
| Profile: name, phone, date_of_birth, gender, notes | edit | name, phone | dob optional, past date | Edit by reception/owner |

#### F-007 Next Patient
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| current_token | read-only | — | Token in `serving` | Name + age shown to doctor only |
| next_tokens | read-only list (3) | — | Next three `arrived` (then `booked`) by position | |
| next_button | action | — | Completes current (`done`) and calls next; idempotent via `Idempotency-Key` | Big button |
| skip_button | action | — | Current → `skipped`; can be recalled | |
| hold_button | action | — | Current → `hold`; reason optional | |
| recall | action | — | `skipped|hold` → `arrived` at front | |
| consult_note_quick | text | no | ≤ 2000 chars; saved to visit | Opens F-008 |

#### F-008 Patient History & Visit Note
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| Timeline: visit_date, doctor, complaint, advice | read-only | — | Newest first | |
| complaint | text | no | ≤ 500 | |
| notes | textarea | no | ≤ 4000 | |
| notes | — | — | — | Private to clinic staff; never shown to the patient |
| medicines_advice | textarea | no | ≤ 2000 | "Dawa / advice"; the only part that can be shared with the patient |
| share_with_patient | checkbox | no | Shown only when clinic `share_advice_with_patient` is ON; default ticked | "Mareez ko dikhayein" (A-014) |
| attachments | file[] | no | jpg/png/pdf, ≤ 5 MB each, ≤ 5 files (P2) | |
| ai_summary | read-only | — | Generated on demand (Phase 4); labelled "AI summary — check before use" | |

#### F-009 TV Screen
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| clinic_name | read-only | — | | |
| per doctor: current_token (very large), next 3 tokens | read-only | — | Up to 4 doctors per screen, rotates if more | No patient names |
| announcement | audio | no | Chime + browser TTS "Token number 12" (Q-005) | Optional |
| connection_indicator | read-only | — | Shows offline after 30 s without update | |

#### F-010 Roz ki Report
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| date | date | yes | Default today | |
| doctor_filter | select | no | | |
| KPIs: patients_seen, avg_wait_minutes, no_shows, online_share | read-only | — | Each drills down to F-004 filtered | |
| chart_7_days | chart | — | Patients per day, last 7 days | |
| export_month | action | no | CSV for a month (P2) | |

#### F-011 Clinic Settings
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| online_booking_enabled | switch | yes | | "Online token ON/OFF" |
| daily_online_limit | int per doctor | yes | 1-500 | "Roz ka token limit" |
| advance_days | int | yes | 0-1 in v1 (today/tomorrow) | |
| default_consult_minutes | int | yes | 2-60 | Used by A-004 |
| time_zone | select | yes | IANA zone | |
| clinic_name, address, phone, maps_url, logo | text/file | name yes | URL valid; logo ≤ 500 KB | |
| language_default | select | yes | `en`, `roman_ur` | |
| share_advice_with_patient | switch | yes | Default OFF | "Mareez ko dawa/hidayat dikhayein" — clinic decides; turning OFF hides already shared advice too |
| ai_notes_enabled | switch | yes | Default OFF; turning ON shows a consent text the owner must accept | "AI ko notes istemal karne dein" (Q-004) |

#### F-012 Staff Login
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| email | email | yes | Valid email; a link is sent only if it belongs to an active `clinic_members` row or platform admin (same message shown either way) | |
| magic_link | emailed link | — | Single use, expires in 15 min; 5 requests per hour per email | Opens the app signed in |
| clinic_choice | select | conditional | Only if member of several clinics | |

#### F-013 New Clinic
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| clinic_name | text | yes | 2-80 | |
| slug | text | yes | `^[a-z0-9-]{3,40}$`, unique | Booking link `/c/{slug}` |
| owner_name | text | yes | | |
| owner_email | email | yes | Valid email | Invited as `owner` (magic link) |
| owner_phone | tel | no | +92 E.164 | Contact only |
| time_zone | select | yes | | |
| status | select | yes | `trial`, `active`, `suspended` | Manual billing |

#### F-014 Clinics List
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| search | text | no | name/slug | |
| Row: name, slug, status, doctors, tokens last 7 days, created_at | read-only | — | | |
| Row action: suspend / activate | action | — | Reason required; audited | |

#### F-015 Staff Management
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| member_name | text | yes | | |
| member_email | email | yes | Valid email, unique per clinic | Login identity |
| member_phone | tel | no | +92 E.164 | Contact only |
| role | select | yes | `owner`, `doctor`, `reception` | |
| linked_doctor_id | select | conditional | Required when role = doctor | |
| active | switch | yes | Deactivation revokes sessions | |

#### F-016 Doctor Management
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| doctor_name | text | yes | | |
| specialty | text | no | | |
| opd_schedule | weekly grid | yes | Per weekday: closed or start-end time; end > start | "OPD timing" |
| daily_online_limit | int | no | Overrides clinic default | |
| consult_minutes | int | no | Overrides clinic default | |
| active | switch | yes | Inactive hides from F-001 | |

#### F-017 AI Activity Log
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| date_range | daterange | yes | | |
| feature_filter | select | no | chat, brief, summary, prediction | |
| Row: time, feature, requested_by, provider/model, tools_called, tokens_used, cost_estimate, outcome | read-only | — | | |

#### F-018 Daily Brief
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| brief_date | date | yes | | |
| brief_text | read-only markdown | — | Generated 21:00 clinic time | |
| anomalies | read-only list | — | Each links to the source records | |
| feedback | thumbs up/down | no | Stored for evaluation | |

#### F-019 Patient Chat Assistant
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| message | text | yes | 1-300 chars; 20 messages per token per day | |
| Reply | read-only | — | Answers only about this token, queue and clinic info; no medical advice | |

#### F-020 Display Device Pairing
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| device_name | text | yes | | e.g. "Waiting room TV" |
| doctor_ids | multi-select | yes | 1-4 doctors | |
| pairing_code | read-only | — | 6 chars, valid 10 min; entered on `/tv` | |
| revoke | action | — | Invalidates the display token | |

#### F-021 Doctor ki Hidayat
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |
| visit_date | read-only date | — | | |
| doctor_name | read-only | — | | |
| medicines_advice | read-only text | — | Shown only if clinic setting ON **and** visit `share_with_patient` = true **and** visit ≤ 30 days old | Never shows `notes` or `complaint` |
| print_or_save | action | no | Browser print / save as PDF | |
| not_shared_message | read-only | — | When any condition is false: "Clinic se rabta karein" | Does not reveal whether a visit exists |

## 6. Key Screen — Detailed Requirements
**F-007 Next Patient (doctor panel)** carries the product.
- Layout: current token card (top, large), NEXT button (full width, ≥ 64 px tall, bottom on mobile), skip/hold as secondary buttons, "Agle 3" list, history drawer (F-008).
- NEXT shall complete the current token and call the next eligible token in one API call (`POST /queues/{doctor_id}/next`) with an `Idempotency-Key`; a double tap shall not advance twice.
- Response budget: API p95 ≤ 300 ms; TV and patient phones updated p95 ≤ 3 s.
- Ordering rule: `arrived` tokens by position first; if none, `booked` tokens by position (patient may be outside) — configurable "call only arrived" setting (default on).
- Error states: network failure shows retry and keeps the button disabled until the outcome is known; conflict (another device advanced) refreshes silently.
- Keyboard: Space/Enter = NEXT, S = skip, H = hold on desktop.

**F-003 Live Queue** must work on low-end Android phones on 3G: first load ≤ 100 KB JS for the route, server-rendered numbers, then Realtime.

## 7. Dashboards
| ID | Dashboard | Role | KPIs (each drills down to records) | Refresh | Phase |
| --- | --- | --- | --- | --- | --- |
| D-001 | Roz ki Report (F-010) | owner, doctor | Patients seen, avg wait, no-shows, online vs walk-in, 7-day trend | Realtime on open + 60 s | 3 |
| D-002 | Platform Overview | platform_admin | Active clinics, tokens today, tokens 7 days, clinics with zero activity 3+ days, AI spend this month | 5 min | 3 |
| D-003 | AI Command Center | owner, platform_admin | AI calls, failures, fallback rate, cost, thumbs-down rate | 5 min | 4 |

## 8. Dashboard UI Standard
KPI card: label (Roman Urdu + English), big number, delta vs yesterday, tap → filtered list. Charts: bar (daily counts) and line (wait trend) only. Filters: date, doctor. States: loading skeleton, empty ("Aaj abhi koi mareez nahi"), error with retry, unauthorized. Numbers are scoped to the caller's clinic and role (doctor sees only own numbers).

## 9. Reports
| ID | Report | Module | Filters | Export | Roles |
| --- | --- | --- | --- | --- | --- |
| R-001 | Daily summary | Reports | date, doctor | screen | owner, doctor |
| R-002 | Monthly report | Reports | month, doctor | CSV (P2), PDF (P3) | owner |
| R-003 | No-show list | Reports | date range, doctor | CSV | owner, reception |
| R-004 | Doctor wait-time report | Reports | date range | screen | owner |
| R-005 | Clinic activity (platform) | Platform | date range | CSV | platform_admin |

## 10. Core Business Workflows

### W-001 Online booking
1. Patient opens `/c/{slug}`; web calls `GET /public/clinics/{slug}` (doctors, OPD, availability).
2. Patient picks doctor, day, enters name and phone, passes Turnstile, submits with `Idempotency-Key`.
3. API checks clinic `active`, booking enabled, OPD exists that day, limit not reached, no active token for same phone+doctor+day.
4. In one transaction: upsert patient (clinic_id, phone, name), lock `token_counters` row (clinic, doctor, date), increment, insert `tokens` (status `booked`, source `online`, `public_code`), insert `token_events`, audit.
5. API publishes queue update; returns token + `public_code`; web redirects to `/t/{public_code}` (F-002).
- **State machine:** `booked -> arrived -> serving -> done`; `booked|arrived -> cancelled`; `serving -> skipped|hold -> arrived`; `booked|arrived -> no_show` (day close)
- **Failure paths:** limit reached → 409 `DAILY_LIMIT_REACHED`, booking closes; duplicate → 409 `ACTIVE_TOKEN_EXISTS` returning the existing link; clinic suspended → 403.

### W-002 Walk-in token
1. Reception opens F-005, types phone; autocomplete offers existing patients.
2. Submit → same service as W-001 with source `walk_in`, status `arrived`.
3. Daily online limit does not block walk-ins unless the owner set a hard cap; overriding is audited.
- **State machine:** as W-001, starting at `arrived`.
- **Failure paths:** doctor has no OPD today → 422 with message.

### W-003 Arrival check-in
1. Reception marks a `booked` token `arrived` in F-004.
2. Event + audit written; queue update published.
- **State machine:** `booked -> arrived`
- **Failure paths:** token already past `arrived` → 409, list refreshes.

### W-004 Call next / skip / hold / recall
1. Doctor presses NEXT: current `serving` → `done` (`completed_at`), next eligible → `serving` (`called_at`).
2. Skip: `serving -> skipped`; Hold: `serving -> hold`; Recall: `skipped|hold -> arrived` with position set before the next eligible.
3. Each step: `token_events` row, audit row, consult duration recorded for estimates, publish update.
- **State machine:** see W-001.
- **Failure paths:** concurrent NEXT from two devices → row lock on queue; second request returns current state with 200 and `already_advanced=true`.

### W-005 Cancel token
1. Patient (F-002, via public code) or reception (F-004, reason required) cancels a `booked|arrived` token.
2. Number is not reused; queue update published.
- **Failure paths:** token already `serving` or later → 409.

### W-006 Day close
1. Cloud Scheduler calls `POST /jobs/day-close` hourly; for each clinic whose local time passed OPD end + 60 min, tokens `booked|arrived|skipped|hold` → `no_show`, `serving` → `done`.
2. Daily stats row `daily_stats` written for the report.
- **Failure paths:** job retried; operation is idempotent per clinic+date.

### W-007 Clinic onboarding
1. Platform admin creates clinic (F-013) with status `trial`.
2. Owner phone is invited (`clinic_members`, role `owner`); owner logs in (W-008), adds doctors (F-016), OPD timing, staff (F-015), pairs TV (F-020).
3. Booking link `/c/{slug}` is shared (WhatsApp, Instagram, Google Maps).
- **State machine:** clinic `trial -> active -> suspended -> active`
- **Failure paths:** slug taken → 409.

### W-008 Staff login
1. Staff enters email → API checks membership → Supabase Auth sends a magic link → staff opens it → Supabase session.
2. Web calls `GET /me`; API verifies JWT, loads memberships; if several clinics, user picks one (stored in httpOnly cookie as `active_clinic_id`, validated every request).
- **Failure paths:** email not a member → same "check your email" message, no link sent (no enumeration); expired/used link → "link expired, request a new one"; > 5 requests per hour → 429.

### W-009 Visit note and AI summary
1. Doctor writes visit note in F-008 (saved to `visits`, audited).
2. If clinic `ai_notes_enabled` is OFF the button is hidden and the API returns 403 `AI_NOTES_DISABLED`. Otherwise the doctor taps "AI summary": API tool `get_patient_history(patient_id)` (permission: doctor of this clinic) → AI provider → summary shown, not stored as a medical record unless the doctor saves it.
- **Failure paths:** AI provider down → Gemini fallback → if both fail, show "summary unavailable" and nothing else changes.

### W-010 Daily brief
1. 21:00 clinic time, job calls `POST /jobs/daily-brief`; agent reads `daily_stats` and anomaly tool output via tools; writes `ai_briefs` row.
2. Owner sees it in F-018.
- **Failure paths:** failure logged in `ai_runs`; retried once at 21:30.

### W-011 Share visit advice with patient
1. Owner turns `share_advice_with_patient` ON in F-011 (audited).
2. Doctor saves a visit in F-008 linked to the current token; "Mareez ko dikhayein" is ticked by default and can be unticked.
3. Patient opens the same token link `/t/{public_code}`; after the token is `done`, F-021 shows the advice.
4. Each view writes an audit row (`visit_advice_viewed`).
- **State machine:** visit advice `private -> shared` (checkbox) ; clinic setting OFF overrides to hidden.
- **Failure paths:** setting OFF, box unticked, or link older than 30 days → neutral "Clinic se rabta karein" message.

## 11. Offline & Synchronization
Not applicable — online-only product. The patient and TV screens show a "connection lost, last updated hh:mm" banner and resume automatically; staff actions require connectivity and are idempotent so a retry after reconnect is safe.

## 12. Database / Data Model

### 12.1 Domains and representative tables
| Domain | Representative tables |
| --- | --- |
| Organization | clinics, clinic_settings, doctors, doctor_schedules |
| Security | users (Supabase `auth.users`), clinic_members, platform_admins, display_devices, audit_logs |
| Patients | patients, visits, visit_attachments |
| Queue | tokens, token_counters, token_events, daily_stats |
| AI | ai_runs, ai_briefs, chat_messages, wait_predictions |

### 12.2 Conventions
`lower_snake_case`, plural tables; UUID v7 primary keys; `created_at`, `updated_at` (timestamptz, UTC); `clinic_id` on every tenant table; soft delete (`deleted_at`) for patients, doctors, members only; tokens are never deleted; optimistic concurrency via `version int` on settings and visits; every FK indexed; composite indexes start with `clinic_id`.

### 12.3 Entity detail
- **clinics**: id, name, slug (unique), status (`trial|active|suspended`), time_zone, address, phone, maps_url, logo_path, created_at.
- **clinic_settings**: clinic_id (PK/FK), online_booking_enabled bool, daily_online_limit int, advance_days int, default_consult_minutes int, call_only_arrived bool, language_default, share_advice_with_patient bool default false, ai_notes_enabled bool default false, ai_consent_accepted_by uuid null, ai_consent_accepted_at timestamptz null, version.
- **doctors**: id, clinic_id, name, specialty, daily_online_limit null, consult_minutes null, active, deleted_at.
- **doctor_schedules**: id, clinic_id, doctor_id, weekday 0-6, start_time, end_time; unique (doctor_id, weekday).
- **clinic_members**: id, clinic_id, user_id (auth.users), name, email (login identity), phone (contact, optional), role (`owner|doctor|reception`), doctor_id null, active; unique (clinic_id, user_id).
- **patients**: id, clinic_id, phone, name, date_of_birth null, gender null, notes; index (clinic_id, phone); trigram index on name.
- **tokens**: id, clinic_id, doctor_id, patient_id, visit_date (date), number int, position numeric, source (`online|walk_in`), status, public_code (unique, 22-char random), estimated_at timestamptz, arrived_at, called_at, completed_at, cancelled_reason; unique (clinic_id, doctor_id, visit_date, number); index (clinic_id, doctor_id, visit_date, status, position).
- **token_counters**: clinic_id, doctor_id, visit_date, last_number; PK (clinic_id, doctor_id, visit_date); locked with `SELECT … FOR UPDATE`.
- **token_events**: id, clinic_id, token_id, from_status, to_status, actor_type (`patient|staff|system|ai`), actor_id, at.
- **visits**: id, clinic_id, patient_id, doctor_id, token_id null, complaint, notes (private), medicines_advice, share_with_patient bool default true, created_by, version.
- **visit_attachments**: id, clinic_id, visit_id, storage_path, mime, size_bytes.
- **daily_stats**: clinic_id, doctor_id, date, seen, no_shows, cancelled, online_count, walk_in_count, avg_wait_minutes, avg_consult_minutes.
- **display_devices**: id, clinic_id, name, doctor_ids uuid[], token_hash, paired_at, revoked_at.
- **audit_logs**: id, clinic_id null, actor_type, actor_id, action, entity, entity_id, before jsonb, after jsonb, request_id, ip_hash, at.
- **ai_runs**: id, clinic_id, feature, requested_by, provider, model, tools_called jsonb, input_tokens, output_tokens, cost_usd numeric(10,6), status, error, at.
- **ai_briefs**: id, clinic_id, date, body_md, anomalies jsonb, feedback.
- **chat_messages**: id, clinic_id, token_id, role (`patient|assistant`), content, at; deleted after 30 days.
- **wait_predictions**: id, clinic_id, token_id, predicted_minutes, model_version, actual_minutes null.

### 12.4 Migration policy
Every schema change ships as an Alembic migration in the same PR; migrations are never edited after merge; CI runs `alembic upgrade head` on an empty database and fails when models differ from migrations (`alembic check`). RLS policies are part of migrations.

### 12.5 Data retention, seed data, sample data
- Tokens, visits, audit logs: kept while the clinic is active; exported and deleted 90 days after a clinic is closed (on request).
- Chat messages: 30 days. AI run logs: 180 days.
- Seed: one demo clinic ("Aapka Clinic"), 2 doctors, 3 staff, 40 tokens across statuses — used by E2E tests and demos.

## 13. API Requirements

### 13.1 Conventions
Base path `/api/v1`; JSON; cursor pagination (`limit`, `cursor`); filters as query params; `Idempotency-Key` header required on POSTs that create tokens or advance queues (stored 24 h); errors as RFC 7807 with `code` field (e.g. `DAILY_LIMIT_REACHED`); `X-Request-ID` echoed; rate limits: public booking 5/min per IP and 3/day per phone per clinic, chat 20/day per token; OpenAPI generated by FastAPI and committed; TS client generated into `packages/api-client`.

### 13.2 Endpoint register
| Area | Endpoint | Methods | Permission | Notes |
| --- | --- | --- | --- | --- |
| Auth | `/api/v1/me` | GET | staff | memberships, active clinic, permissions |
| Auth | `/api/v1/me/active-clinic` | PUT | staff | switch clinic |
| Public | `/api/v1/public/clinics/{slug}` | GET | public | clinic info, doctors, availability |
| Public | `/api/v1/public/clinics/{slug}/tokens` | POST | public + Turnstile | W-001 |
| Public | `/api/v1/public/tokens/{public_code}` | GET | public (code) | F-002/F-003 data |
| Public | `/api/v1/public/tokens/{public_code}/cancel` | POST | public (code) | W-005 |
| Public | `/api/v1/public/tokens/{public_code}/chat` | POST | public (code) | F-019, Phase 4 |
| Public | `/api/v1/public/tokens/{public_code}/advice` | GET | public (code) + clinic setting + visit flag | F-021, W-011 |
| Tokens | `/api/v1/tokens` | GET, POST | reception, owner, doctor(GET own) | list day; walk-in create |
| Tokens | `/api/v1/tokens/{id}/arrive` | POST | reception, owner | W-003 |
| Tokens | `/api/v1/tokens/{id}/cancel` | POST | reception, owner | W-005 |
| Queue | `/api/v1/queues/{doctor_id}` | GET | doctor(self), reception, owner | current + next |
| Queue | `/api/v1/queues/{doctor_id}/next` | POST | doctor(self) | W-004 |
| Queue | `/api/v1/queues/{doctor_id}/skip` · `/hold` · `/recall/{token_id}` | POST | doctor(self) | W-004 |
| Patients | `/api/v1/patients` | GET | reception, owner, doctor | search |
| Patients | `/api/v1/patients/{id}` | GET, PATCH | GET all staff; PATCH reception, owner | |
| Visits | `/api/v1/patients/{id}/visits` | GET, POST | doctor; GET owner | F-008 |
| Visits | `/api/v1/visits/{id}` | PATCH | doctor (author) | |
| Visits | `/api/v1/visits/{id}/ai-summary` | POST | doctor | Phase 4 |
| Reports | `/api/v1/reports/daily` · `/weekly` · `/monthly.csv` | GET | owner, doctor(own) | D-001, R-001..R-004 |
| Settings | `/api/v1/settings` | GET, PUT | owner | F-011 |
| Doctors | `/api/v1/doctors` · `/{id}` · `/{id}/schedule` | GET, POST, PATCH, PUT | owner (GET all staff) | F-016 |
| Staff | `/api/v1/members` · `/{id}` | GET, POST, PATCH | owner | F-015 |
| Display | `/api/v1/displays` · `/{id}/revoke` | GET, POST | owner | F-020 |
| Display | `/api/v1/display/pair` · `/display/state` | POST, GET | pairing code / display token | F-009 |
| AI | `/api/v1/ai/runs` · `/ai/briefs` | GET | owner, platform_admin | F-017, F-018 |
| Admin | `/api/v1/admin/clinics` · `/{id}` · `/{id}/status` | GET, POST, PATCH | platform_admin | F-013, F-014 |
| Admin | `/api/v1/admin/overview` | GET | platform_admin | D-002 |
| Jobs | `/api/v1/jobs/day-close` · `/daily-brief` · `/estimates` | POST | service token (Cloud Scheduler OIDC) | W-006, W-010 |
| Health | `/api/v1/health` | GET | public | liveness + DB check |

### 13.3 Integrations (external)
| ID | System | Direction | Protocol | Auth | Failure handling | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| I-001 | Supabase Auth (email magic link; custom SMTP: Gmail app password in dev, own-domain sender in prod per Q-007) | out/in | HTTPS, JWT/JWKS | Service key server-side only | Show retry; JWKS cached 10 min | 0 |
| I-002 | Supabase Realtime broadcast | out | HTTPS publish | Service key server-side | Publish failure logged; clients fall back to polling | 1 |
| I-003 | Cloudflare Turnstile | in | HTTPS verify | Secret key | Fail closed on public booking; reception unaffected | 1 |
| I-004 | OpenRouter | out | HTTPS (OpenAI-compatible) | API key | Timeout 20 s → I-005 | 4 |
| I-005 | Google Gemini API | out | HTTPS | API key | Timeout 20 s → feature shows "unavailable" | 4 |
| I-006 | Sentry | out | HTTPS | DSN | Non-blocking | 0 |
| I-007 | WhatsApp/SMS reminders | out | HTTPS | Provider key | Deferred (§3.2) | — |

## 14. Security & Audit
- HTTPS in all non-development environments.
- Role-based authorization enforced by the API (the UI hiding an action is convenience, not security).
- No credentials or secrets in source control; `.env.example` holds keys with empty values.
- Staff authentication only through Supabase Auth email magic links (single use, 15 min expiry); rate limiting on auth and all public endpoints.
- SMTP credentials (including the development Gmail app password) live only in the Supabase dashboard; the app password is revoked if leaked, and each environment uses its own app password.
- Validation on all user input and API payloads; SQLAlchemy only, no string-built SQL.
- Phone numbers and names masked in logs; Sentry scrubbing enabled.
- Public codes are 128-bit random; display tokens stored only as hashes.
- Supabase service-role key exists only in the API runtime.

### 14.1 Audited actions
Token create/arrive/cancel/next/skip/hold/recall/no-show; walk-in over limit; patient create/edit/merge; visit create/edit; settings change (including `share_advice_with_patient` and `ai_notes_enabled`); patient view of shared advice; doctor and schedule change; member invite/role change/deactivate; display pair/revoke; clinic create/status change; data export; every AI run (in `ai_runs`); login success/failure.

### 14.2 Roles and permission matrix
| Role | Modules / screens | Actions (view, create, edit, delete, approve, export, post, reverse) |
| --- | --- | --- |
| Patient (public, by code) | F-001, F-002, F-003, F-019, F-021 | create own token, view own token, cancel own token, chat, view advice the clinic chose to share |
| Reception | F-004, F-005, F-006 | view day list, create walk-in, mark arrived, cancel, view/edit patient |
| Doctor | F-007, F-008, F-004 (own), F-010 (own) | advance own queue, skip/hold/recall, view history, create/edit own visit notes, AI summary |
| Owner | All clinic screens, F-010, F-011, F-015, F-016, F-017, F-018, F-020 | everything in reception, settings, doctors, staff, displays, view reports, export |
| Display device | F-009 | view queue numbers of assigned doctors |
| Platform admin | F-013, F-014, D-002, F-017 (all) | create clinic, change status, view platform stats; **no** access to patient data or visit notes |

### 14.3 Data protection and privacy
Health data (visit notes) and personal data (name, phone) are confidential. Encryption in transit (TLS) and at rest (Supabase default). Visit `notes` are visible only to doctors and owner of that clinic. `medicines_advice` is shown to the patient only through W-011 when the clinic allows it. Patients can ask the clinic to delete their profile; the owner can anonymise a patient (name → "Deleted", phone → hash) while keeping counts. Backups are encrypted by the provider. Clinics are in Pakistan: the product follows PECA 2016 and the principles of Pakistan's Personal Data Protection Bill (consent, purpose limitation, security, deletion on request) and is ready to adapt if it is enacted.

### 14.4 Threat notes
| Threat | Control |
| --- | --- |
| Bots flooding public booking to fill the daily limit | Turnstile, per-IP and per-phone limits, one active token per phone/doctor/day, owner can switch online booking off |
| Cross-clinic data access (IDOR) | Scoped session + RLS + tests on every endpoint |
| Guessing token links to read names | 128-bit public codes; public token view shows first name initial only |
| Prompt injection via chat or notes | Tools are read-only and scoped to the token/patient in context; system prompt forbids other topics; output never executed |
| Stolen TV display link | Display token is read-only, shows numbers only, revocable |
| Forwarded token link exposes shared advice | Advice visible only 30 days, only when clinic and doctor allow it; shows no diagnosis or private notes |

## 15. AI-Assisted Development Protocol
| Step | Developer / agent requirement |
| --- | --- |
| 1. Requirement | A small, testable story with acceptance criteria |
| 2. Context | Supply structure, conventions, constraints (`context/` folder) |
| 3. Design | Agree database/API/UI design before large generation (`/architect`) |
| 4. Generate | Scaffolding, implementation, refactoring, tests |
| 5. Review | A human reviews all generated code, queries, security, error handling (`/review`) |
| 6. Test | Acceptance tests written first and passing; `scripts/verify.sh` green |
| 7. PR | Requirement, test evidence, migration notes |
| 8. Merge | Only approved, passing PRs reach protected branches |

The development team remains accountable for architecture, security, correctness and maintainability. AI tooling is never given unrestricted production credentials or unrestricted database write access.

## 16. UI/UX Standards
- `motion: minimal` for staff screens and TV; `refined` (subtle transitions on number change) for patient screens.
- Palette direction: calm clinical teal/green primary with deep slate (as in the blueprint), amber for owner screens, high-contrast TV theme (dark background, green numbers).
- Mobile-first; breakpoints 360 / 768 / 1280; TV layout targets 1920×1080 at 3 m viewing distance (current number ≥ 25 % of screen height).
- Strings in `messages/en.json` and `messages/roman-ur.json` (next-intl); no strings hard-coded in components.
- WCAG 2.2 AA; touch targets ≥ 44 px; status never shown by colour alone (badge text).
- Four states on every screen: loading, empty, error, unauthorized.
- Times formatted in clinic time zone through one formatting module.

## 17. Performance Requirements
| Area | Target / requirement | How verified |
| --- | --- | --- |
| Standard interaction | API p95 ≤ 300 ms (warm) | Load test in Phase 2 |
| Search | Patient search p95 ≤ 300 ms with 50k patients per clinic | Seeded perf test |
| Transaction posting | Token create p95 ≤ 400 ms; 50 concurrent bookings on one doctor produce unique numbers | Concurrency test |
| Reports | Daily report ≤ 1 s from `daily_stats`; heavy reports must not block transactional operations | Test |
| Concurrency | 20 clinics × 300 live viewers within free-tier Realtime limits (verify current limits) | Synthetic test |
| Database | All tenant queries use a `clinic_id` index (no seq scans on tokens > 10k rows) | `EXPLAIN` check in CI |
| Patient page | Live queue route ≤ 100 KB JS, LCP ≤ 2.5 s on simulated slow 4G | Lighthouse CI |
| Cold start | API cold start ≤ 3 s; keep-warm ping during OPD hours | Monitoring |

## 18. Backup & Disaster Recovery
RPO 24 h, RTO 4 h (free tier). Supabase daily backups (verify free-tier retention) plus a nightly `pg_dump` from GitHub Actions to encrypted storage, kept 14 days. A monthly CI job restores the latest dump into a scratch database and runs smoke queries. On-call: the developer; incident notes in `docs/incidents/`.

## 19. Testing & Acceptance
| Test level | Scope | Tooling |
| --- | --- | --- |
| Unit | Token numbering, state machine, estimate formula, OPD/day rules | pytest |
| Architecture | Routers don't import models directly; every endpoint has a permission dependency; every tenant query scoped | pytest + import-linter |
| Integration | API + Postgres + RLS + auth + audit; cross-clinic 404 tests per endpoint | pytest + Postgres container |
| Component / UI | Forms, validation, role-based visibility, responsive | Vitest + Testing Library |
| E2E | Book online → arrive → NEXT → TV & patient page update; walk-in; owner settings | Playwright |
| Offline | Not applicable — reconnect banner tested in E2E | Playwright |
| Performance | §17 targets | k6 / Lighthouse CI |
| Security | Dependency scan, secret scan, authz tests, rate-limit tests | GitHub Dependabot, gitleaks |

## 20. Acceptance Criteria for Forms
Every form: layout per §5.1; only fields in §5.3; client and server validation with the same rules; inline Roman Urdu/English errors; double-submit safe; permissions enforced by API; audit written for audited actions; four states; keyboard flow; works at 360 px.

## 21. Acceptance Criteria for Dashboards
Every KPI drills down to the matching F-004 list; numbers reconcile with `tokens` for the day; doctor sees only own numbers; loads ≤ 1 s; empty day shows empty state, not zeros with errors.

## 22. Phased Delivery Plan
| Phase | Scope | Exit criteria (a test a person can run) |
| --- | --- | --- |
| 0 | Foundation (weeks 1-2): monorepo, CI, Docker Compose, Alembic, Supabase projects, staff login (F-012), tenancy + RLS + audit skeleton, platform admin F-013/F-014, staff F-015, design tokens, i18n, Sentry, deploy staging | Admin creates a clinic, owner logs in with an email magic link, adds a reception user; a second clinic's owner gets 404 on the first clinic's data; CI green |
| 1 | Patient + queue core (weeks 3-4): doctors & OPD (F-016), booking F-001, confirm F-002, live queue F-003, token numbering, Turnstile, Realtime publish | From a phone, book 2 tokens for the same doctor; numbers are 1 and 2; limit reached closes booking; concurrency test passes |
| 2 | Reception, doctor, TV (weeks 5-7): F-004, F-005, F-006, F-007, F-008, F-009, F-020, F-021, day close job | Online + walk-in tokens in one list; doctor presses NEXT and TV + patient phone change within 3 s; day close marks no-shows; with sharing ON the patient sees the doctor's advice on the token link, with sharing OFF they do not |
| 3 | Owner (weeks 8-9): F-010/D-001, F-011, R-001..R-004, D-002, pilot hardening, backups + restore test | Owner turns online booking off and the booking page closes; daily report numbers match the token list; restore test passes; pilot clinic live |
| 4 | AI and add-ons (weeks 10-12): AI tool layer, F-019 chat, F-018 brief, AI summary in F-008, wait-time prediction, F-017, D-003, CSV export, TV voice (Q-005) | Patient asks "mera number kab aayega" and gets the correct number of people ahead; brief generated at 21:00; every AI call appears in F-017; Gemini fallback works when OpenRouter key is disabled |

## 23. Required Deliverables
- Complete source code and full repository history
- Database migrations and ERD / database documentation
- API documentation (OpenAPI)
- All forms and dashboards listed in §5 and §7
- Unit, integration and E2E tests
- Deployment scripts and environment configuration guide
- Backup/restore guide
- Administrator manual (platform admin + clinic owner) and user manual (reception, doctor) in Roman Urdu + English
- Clinic onboarding checklist and TV pairing guide
- Training session for pilot clinic staff (blueprint step 4) and handover of accounts (step 5)

## 24. Definition of Done
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

## 25. Change Control
Any feature, form, report, integration or workflow not in this PRD is handled by a change request recording: scope, business reason, effort, impact on schedule and cost, affected sections, decision, approver. Approved changes are recorded in §0.2 and, for stack or architecture changes, as an ADR in `docs/adr/`.

### 25.1 Change request log
| CR | Date | Requester | Summary | Sections | Decision | Approver |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | — | None yet | — | — | — |

## 26. Initial Feature Priority
| Priority | Meaning | Items |
| --- | --- | --- |
| P0 — Mandatory MVP | Cannot ship without | F-001, F-002, F-003, F-004, F-005, F-007, F-009, F-011, F-012, F-013, F-014, F-015, F-016, F-020; tenancy, audit, Realtime, day close |
| P1 — Commercial release | Needed before second clinic | F-006, F-008, F-021, F-010/D-001, D-002, R-001, R-003, R-004, F-017, wait-time prediction |
| P2 — Expansion | Add-ons from blueprint | F-018, F-019, CSV export R-002, attachments, browser reminders, token slip print, TV voice |
| P3 — Differentiation | Later | WhatsApp/SMS reminders, online payment, subscription billing, multi-branch, Urdu RTL, PDF reports |

## 27. Final Product Structure
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

## 28. Approval
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Product owner | (Q-006) | pending | |
| Technical lead | (Q-006) | pending | |

## 29. Visual UI / UX Wireframes — Dashboards

### 29.1 D-001 Roz ki Report
```
+--------------------------------------------+
| Roz ki Report        [Aaj ▾] [Doctor ▾]    |
+--------------------------------------------+
| Patients seen | Avg wait  | No-shows | Online share |
|     54        |  14m      |    6     |    38 %      |
+--------------------------------------------+
| 7 din ka chart  ▇ ▆ ▇ █ ▆ ▇ █              |
+--------------------------------------------+
| [Mahine ki report download] (P2)           |
+--------------------------------------------+
```

### 29.2 D-002 Platform Overview
```
+------------------------------------------------------------+
| Active clinics | Tokens today | Tokens 7d | Idle clinics | AI spend |
+------------------------------------------------------------+
| Clinics table: name | status | tokens 7d | last activity    |
+------------------------------------------------------------+
```

### 29.3 D-003 AI Command Center
```
+------------------------------------------------------------+
| AI calls | Failures | Fallback rate | Cost | Thumbs-down     |
+------------------------------------------------------------+
| Recent runs (→ F-017)                                        |
+------------------------------------------------------------+
```

## 30. Visual Form Wireframes

### 30.1 F-001 Token Booking
```
+------------------------------+
| [logo] Aapka Clinic          |
| Token Booking                |
+------------------------------+
| doctor_id:  [General OPD ▾]  |
| visit_date: (•) Aaj ( ) Kal  |
| patient_name: [__________]   |
| phone:        [+92 ______]   |
| [Turnstile]                  |
+------------------------------+
| [   TOKEN LO   ]             |
+------------------------------+
```

### 30.2 F-002 Token Confirm
```
+------------------------------+
|        ✓ Token Confirm       |
|        APNA TOKEN            |
|           #18                |
| estimated_time: 11:40 AM     |
| doctor_name: Dr. ...         |
+------------------------------+
| [ LIVE QUEUE DEKHEIN ]       |
| [cancel_token]               |
+------------------------------+
```

### 30.3 F-003 Live Queue
```
+------------------------------+
| Live Queue      ● live       |
| current_token:  #12          |
| my_token:       #18          |
| people_ahead:   6            |
| estimated_wait_minutes: 35   |
| last_updated: 5s ago         |
+------------------------------+
| [reminder_toggle]  [Chat ?]  |
+------------------------------+
```

### 30.4 F-004 Aaj ki List
```
+-------------------------------------------------------+
| Aaj ki List   date [Aaj]  doctor_filter [All ▾]       |
| status_filter [▾]   search [ naam / phone ]           |
+-------------------------------------------------------+
| #12 Mareez A  ***4567 online   [SERVING]              |
| #13 Mareez B  ***1122 walk_in  [ARRIVED]              |
| #14 Mareez C  ***9988 online   [BOOKED] [mark_arrived]|
+-------------------------------------------------------+
| last updated 10:42 by Reception                        |
+-------------------------------------------------------+
```

### 30.5 F-005 Walk-in Entry
```
+---------------------------------+-------------------+
| Walk-in Entry                   |  NAYA TOKEN       |
| phone:        [+92 ______]      |     #19           |
| patient_name: [__________]      |  Print (P2)       |
| doctor_id:    [General OPD ▾]   |                   |
| [ ] ignore_daily_limit          |                   |
| [ TOKEN BANAO ]                 |                   |
+---------------------------------+-------------------+
```

### 30.6 F-007 Next Patient
```
+------------------------------+
| Doctor Panel     Dr. ...     |
| current_token  #12           |
| Mareez name, age             |
| next_tokens: #13 #14 #15     |
+------------------------------+
| [skip_button] [hold_button]  |
| [        NEXT ▶        ]     |
+------------------------------+
| consult_note_quick → F-008   |
+------------------------------+
```

### 30.7 F-009 TV Screen
```
+--------------------------------------------------+
| AAPKA CLINIC — OPD                                |
| ABHI CHAL RAHA          |  AGLE                   |
|                         |  #13                    |
|      #12                |  #14                    |
|                         |  #15                    |
+--------------------------------------------------+
```

### 30.8 F-011 Clinic Settings
```
+------------------------------+
| Settings                     |
| online_booking_enabled  [ON] |
| daily_online_limit      [40] |
| default_consult_minutes [8]  |
| time_zone [Asia/Karachi ▾]   |
| share_advice_with_patient [OFF] |
| ai_notes_enabled        [OFF] |
| → Doctors (F-016) / OPD      |
| [ SAVE ]                     |
+------------------------------+
```

### 30.9 F-012 Staff Login
```
+------------------------------+
|        [logo] Aapka Clinic   |
|          Staff Login         |
| phone: [+92 ______]          |
| email: [_____________]       |
| "Login link email kar diya"  |
| [ LOGIN ]                    |
+------------------------------+
```

### 30.10 F-013 New Clinic
```
+------------------------------+
| New Clinic                   |
| clinic_name [__________]     |
| slug        [aapka-clinic]   |
| owner_name  [__________]     |
| owner_email [__________]     |
| owner_phone [+92 ______]     |
| time_zone   [▾]  status [trial ▾] |
| [ CREATE ]                   |
+------------------------------+
```

### 30.11 F-014 Clinics List
```
+------------------------------------------------------+
| Clinics   search [______]            [+ New Clinic]  |
| name | slug | status | doctors | tokens 7d | created  |
| ...                         [suspend]/[activate]     |
+------------------------------------------------------+
```

### 30.12 F-015 Staff Management
```
+------------------------------------------------------+
| Staff                                   [+ Add]      |
| member_name | member_email | member_phone | role | linked_doctor_id | active |
+------------------------------------------------------+
```

### 30.13 F-016 Doctor Management
```
+------------------------------------------------------+
| doctor_name [______]  specialty [______]             |
| opd_schedule: Mon [09:00]-[13:00] ... Sun [closed]   |
| daily_online_limit [__]  consult_minutes [__]  active|
| [ SAVE ]                                             |
+------------------------------------------------------+
```

### 30.14 F-020 Display Device Pairing
```
+------------------------------+
| device_name [Waiting room TV]|
| doctor_ids  [x] Dr A [x] Dr B|
| pairing_code:  K7P-2QX       |
| (enter on /tv within 10 min) |
| [revoke]                     |
+------------------------------+
```

### 30.15 F-021 Doctor ki Hidayat
```
+------------------------------+
| [logo] Aapka Clinic          |
| Doctor ki Hidayat            |
| visit_date: 31 Oct           |
| doctor_name: Dr. ...         |
| medicines_advice:            |
|  - ...                       |
| [print_or_save]              |
+------------------------------+
```

## 31. Visual Design Rules for Implementation
Tokens only (CSS variables via Tailwind theme), no hard-coded colours; 4 px spacing scale; reuse shadcn/ui components and check `context/ui-registry.md` before creating a new one; one icon set (lucide); token numbers use a tabular monospace numeral style; role accent colours: patient teal, reception blue, doctor purple, TV dark green, owner amber, login slate (matches blueprint).

## 32. UI Acceptance Checklist
- [ ] Layout matches §5.1
- [ ] Every field is in §5.3 (no invented fields)
- [ ] Inline validation, actionable error messages
- [ ] Unauthorized actions hidden or disabled; API still enforces
- [ ] Loading, empty, error, unauthorized states present
- [ ] Keyboard navigation complete
- [ ] Responsive on the target devices (360 px phone, tablet, desktop, 1080p TV)
- [ ] Audit/status panel present where required
- [ ] All strings come from the i18n files (English + Roman Urdu)

## 33. Note on Final UI Design
The visual identity is provisional and follows the blueprint's style. Only token values (colour, type, radius) change later; workflows and information architecture do not.

## 34. Mandatory Compliance / Regulatory Integration Requirement
No tax or e-invoicing authority integration applies (the product does not invoice). Clinics are in Pakistan: PECA 2016 applies, and the product follows the principles of the Personal Data Protection Bill so it is ready if the Bill is enacted. The controls in §14.3 are P0.

### 34.1 Integration Scope
Not applicable — no regulator integration; obligations are data-handling rules, not data submission.
### 34.2 Transaction Flow
Not applicable — no regulated transaction submission.
### 34.3 Integration Statuses
| Status | Meaning | Next allowed states |
| --- | --- | --- |
| n/a | No regulator submission | n/a |
### 34.4 Integration Form
Not applicable.
### 34.5 Failure Handling
Not applicable.
### 34.6 Reporting & Reconciliation
Patient data export/deletion requests are handled by the clinic owner and logged in `audit_logs`.
### 34.7 Security Requirements
As §14; AI processing of visit notes requires the clinic to switch `ai_notes_enabled` ON and accept the consent text; sharing advice with patients requires `share_advice_with_patient` ON.
### 34.8 Acceptance Criteria
Owner can anonymise a patient; export and anonymisation are audited; AI summary is disabled for a clinic that has not accepted the AI data-processing terms.

## 35. Mandatory P0 Compliance Requirement
P0 before go-live (Phase 3): privacy notice on booking page, clinic on/off settings for AI use of notes and for sharing advice with patients (both default OFF), patient anonymisation (§14.3), audit log of data access to visit notes. Delivered in Phases 2-3.

## 36. Mandatory Agentic AI Architecture

### 36.1 Agentic AI Product Vision
Reduce phone calls and guesswork: patients get plain answers about their turn, doctors get a 5-line history summary, owners get a nightly brief, and estimates get more accurate over time.
### 36.2 Agentic AI Architecture
User → `apps/api/app/ai` agent → approved tool → domain service (with the caller's identity, clinic scope and permissions) → database. Providers: OpenRouter (primary model chosen per feature, configurable), Gemini (fallback). The AI layer is a client of the services, never of the database.
### 36.3 AI Must Not Have Direct Database Authority
The AI layer shall not hold database credentials or run arbitrary SQL. All data access passes through the tools below, which enforce clinic scope and user permissions. All AI tools in v1 are read-only except writing its own `ai_runs`, `ai_briefs`, `chat_messages` and `wait_predictions` rows through services.
### 36.4 AI Tool / Function Layer
| Tool | Purpose | Read/Write | Required permission | Approval level |
| --- | --- | --- | --- | --- |
| `get_my_token_status(public_code)` | Chat: own token, people ahead, estimate | Read | Public code of the chat | None |
| `get_clinic_info(clinic_id)` | Chat: timings, address, doctors | Read | Public | None |
| `get_patient_history(patient_id)` | Visit summary | Read | Doctor of clinic | Doctor triggers |
| `get_daily_stats(clinic_id, date_range)` | Brief | Read | Owner / system job | None |
| `detect_anomalies(clinic_id, date)` | Brief | Read | Owner / system job | None |
| `get_consult_durations(doctor_id, n)` | Prediction | Read | System job | None |
| `save_wait_prediction(token_id, minutes)` | Prediction | Write (own table) | System job | None (shown as estimate only) |
### 36.5 Specialized Agents
| Agent | Responsibility | Tools it may call | Autonomy level |
| --- | --- | --- | --- |
| Patient Chat | Answer token/queue/clinic questions in Roman Urdu/English | get_my_token_status, get_clinic_info | L1 |
| Visit Summarizer | Summarise past visits for the doctor | get_patient_history | L1 |
| Daily Brief | Nightly summary + anomalies for owner | get_daily_stats, detect_anomalies | L1-L2 |
| Wait Predictor | Better estimate per token | get_consult_durations, save_wait_prediction | L4 within limits (writes estimate only) |
### 36.6 AI Autonomy Levels
L1 explain · L2 recommend · L3 draft (approval required) · L4 act within limits · L5 fully autonomous. Chat and Summarizer are L1; Brief L2; Predictor L4 limited to writing an estimate. Promotion requires 4 weeks of evaluation data and owner approval via §25.
### 36.7 AI Approval Center
Not applicable in v1 — no agent performs an action that needs approval. Revisit if an agent ever changes tokens or messages patients.
### 36.8 AI Command Center Dashboard
D-003 (§7, §29.3).
### 36.9 AI Agent Activity / Audit Form
F-017. Every run logs: who asked (patient code / user / system), agent, provider, model, tools called with arguments (PII masked), tokens, cost, outcome, fallback used.
### 36.10 Agent Requirements — Patient Chat
Shall answer only from tool results; shall refuse medical advice with a fixed message to contact the clinic; shall reply in the patient's language (Roman Urdu or English); p95 reply ≤ 6 s; 20 messages/day per token.
### 36.11 Agent Requirements — Visit Summarizer
Shall summarise at most the last 10 visits into ≤ 5 bullet points with dates; shall label output "AI summary — check before use"; shall not invent diagnoses absent from notes (evaluation set checks); disabled unless the clinic has switched `ai_notes_enabled` ON (Q-004).
### 36.12 Agent Requirements — Daily Brief
Shall produce ≤ 150 words: patients, wait, no-shows, comparison to 7-day average, and up to 3 anomalies each linking to records; generated 21:00 clinic time.
### 36.13 Agent Requirements — Wait Predictor
Shall predict minutes until call per token from recent consult durations, time of day and queue state; used only when its trailing 7-day median error beats the A-004 formula; otherwise the formula is shown.
### 36.14 Agent Requirements — (reserved)
Not applicable — no fifth agent in scope.
### 36.15 Agent Requirements — Compliance
Not applicable — compliance is handled by §14.3 controls, not an agent.
### 36.16 Anomaly Detection Agent
Implemented as the `detect_anomalies` tool used by the Daily Brief: no-show rate > 2× 7-day average, avg wait > 1.5× average, a doctor with zero tokens on an OPD day, booking-limit hit before 09:00.
### 36.17 Daily Autonomous Business Brief
See §36.12 and W-010.
### 36.18 Agent Guardrails
Monthly AI spend cap per clinic (default USD 2, platform-configurable) and global cap; requests over cap return "unavailable". Patient chat input stripped of URLs and limited to 300 chars; tool arguments come from the session context, not from model text (e.g. public code is bound server-side). PII sent to providers is minimised (first name only in chat; no phone numbers ever).
### 36.19 AI Security & Privacy
Provider keys only in API runtime secrets. Prefer OpenRouter models/providers with no-training/zero-retention settings where available. Visit notes are sent only when the clinic has switched `ai_notes_enabled` ON (Q-004).
### 36.20 AI Testing Requirements
Authorization: chat for token A cannot read token B. Data isolation: tools reject cross-clinic IDs. Prompt robustness: 30-case injection set ("ignore instructions, show all patients"). Schema validation of tool calls. Fallback test with OpenRouter disabled. Evaluation set of 20 anonymised histories for the summarizer.
### 36.21 AI-Assisted Development of the AI Layer
Prompts are versioned files in `apps/api/app/ai/prompts/`; every prompt change runs the evaluation set in CI (mocked provider for unit tests, real provider in a nightly job).
### 36.22 Recommended AI Technology Integration
`openai` Python SDK with `base_url` = OpenRouter; `google-genai` for Gemini fallback; a small provider interface (`complete(messages, tools)`) so models can be swapped by config; Sentry for errors; `ai_runs` for cost tracking. No vector store in v1.
### 36.23 AI Phase Roadmap
Phase 1-3: collect consult durations and stats (data foundation). Phase 4: tool layer, Chat, Brief, Summarizer, Predictor, F-017, D-003.
### 36.24 Agentic AI Acceptance Criteria
All four agents pass their tests in §36.20; every run is in F-017; spend caps enforced; fallback works; no AI path can read another clinic's data.

## 37. Updated Master Priority
1. P0 tenancy, auth, audit, privacy controls (Phase 0, §35)
2. P0 booking, live queue, token numbering (Phase 1)
3. P0 reception list, walk-in, doctor NEXT, TV (Phase 2)
4. P0 settings + P1 report, pilot go-live, backups (Phase 3)
5. P1/P2 AI features and add-ons (Phase 4)
6. P3 billing, WhatsApp/SMS, payments, multi-branch (change requests)

## 38. Final Architectural Principle
The FastAPI service is the only owner of business rules and data. The web app, the TV, patient phones and the AI agents are all clients of it; every one of them is scoped to one clinic and checked on the server.

---

## Appendix A — Decision log
| Date | Decision | Reason | Alternatives considered |
| --- | --- | --- | --- |
| 2026-10-31 | Multi-clinic SaaS, production profile | Owner answer | Single clinic MVP |
| 2026-10-31 | Next.js + FastAPI + Supabase Postgres | Owner answer | Next.js + Supabase only |
| 2026-10-31 | Supabase Realtime broadcast published by API | Free, works with scale-to-zero API | FastAPI WebSockets |
| 2026-10-31 | No clinic billing until 1-2 clinics live | Owner answer | Stripe from day one |
| 2026-10-31 | OpenRouter + Gemini fallback | Owner answer | Single provider |
| 2026-10-31 | Clinics in Pakistan only | Owner answer | Pakistan + India |
| 2026-10-31 | Staff login by email magic link | Owner answer; no SMS cost | Phone OTP |
| 2026-10-20 | Development Supabase project sends auth email through custom SMTP (Gmail app password) | Built-in sender allows ~2 emails/hour per project | Built-in Supabase sender |
| 2026-10-31 | Clinic on/off settings for sharing advice with patients and for AI use of notes | Owner: "it depends on them" | Always share / never share |

## Appendix B — Risks
| ID | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| RK-01 | Vercel Hobby is non-commercial | High | Medium | Move to Vercel Pro or Cloudflare at first paying clinic (A-010) | Product owner |
| RK-02 | Built-in Supabase sender (~2 emails/hour) blocks logins; Gmail SMTP in dev has a daily sending cap and personal-account branding | Medium | Medium | Gmail SMTP in all environments (owner decision); watch the daily cap and spam rate; switch to an own-domain sender per §3.2 trigger | Developer |
| RK-03 | Supabase free tier limits (DB size, Realtime connections, project pause on inactivity) | Medium | High | Monitor usage in D-002; upgrade trigger at 70 % of any limit | Developer |
| RK-04 | Cloud Run cold start delays NEXT | Medium | Medium | Keep-warm ping during OPD hours | Developer |
| RK-05 | One developer, 10-12 weeks for 20 screens + AI | High | High | AI and P2 items in Phase 4 can slip without blocking pilot | Product owner |
| RK-06 | Bot bookings fill daily limit | Medium | Medium | §14.4 controls | Developer |
| RK-07 | Health data sent to AI providers without consent | Low | High | `ai_notes_enabled` default OFF + consent text (Q-004) | Product owner |

## Appendix C — Cost and infrastructure profile
| Service | Tier / plan | Limit that matters | Est. monthly cost |
| --- | --- | --- | --- |
| Supabase (DB, Auth, Realtime, Storage) | Free | DB size, Realtime concurrent connections, pause after inactivity (verify current limits) | USD 0 (Pro ~USD 25 when exceeded) |
| Vercel | Hobby → Pro | Non-commercial on Hobby | USD 0 → ~20 |
| Google Cloud Run | Free tier | Monthly request/CPU allowance | USD 0 |
| Cloud Scheduler | Free tier | Number of jobs | USD 0 |
| Cloudflare Turnstile | Free | — | USD 0 |
| Sentry | Developer (free) | Monthly events | USD 0 |
| OpenRouter / Gemini | Pay as you go / free tier | Spend cap §36.18 | ~USD 0-5 for 2 clinics |
| Email for magic links — development | Gmail SMTP with app password | Gmail daily sending cap (verify) | USD 0 |
| Email for magic links — production | Gmail SMTP (owner decision); own-domain sender when §3.2 trigger fires | Gmail daily cap (verify) | USD 0 |
