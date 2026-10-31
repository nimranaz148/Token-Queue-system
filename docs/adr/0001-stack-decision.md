# ADR 0001 — Stack decision

- **Status:** accepted
- **Date:** 2026-10-31
- **Source:** `docs/prd/PRD.md` §3 (v0.2.2), discovery log

## Context

Multi-clinic SaaS for Pakistani clinics (token booking, live queue, reception list, doctor panel, waiting-room TV, owner reports, four AI features). Production profile, free-tier budget, one developer, ~10-12 weeks. Patients use cheap Android phones and never log in; staff log in by email magic link. Live queue updates must reach phones and TVs within 3 s (p95).

## Decision

| Layer | Choice |
| --- | --- |
| Web | Next.js (App Router, TypeScript strict), Tailwind CSS v4, shadcn/ui, React Hook Form + Zod, TanStack Query, next-intl (English + Roman Urdu), Recharts — `apps/web`, hosted on Vercel |
| API | FastAPI + Pydantic v2, SQLAlchemy 2 (async), Alembic, `uv` — `apps/api`, hosted on Google Cloud Run |
| Database | PostgreSQL on Supabase, RLS on every tenant table as a second guard |
| Auth | Supabase Auth email magic links via custom SMTP (Gmail app password); API verifies JWTs with JWKS |
| Realtime | Supabase Realtime broadcast, published only by the API; 15 s polling fallback |
| Contract | OpenAPI from FastAPI → `packages/api-client` (openapi-typescript), drift checked by the `contract` lane |
| AI | `apps/api/app/ai`: OpenRouter (OpenAI-compatible SDK) primary, Google Gemini fallback, through a permission-checked tool layer |
| Jobs | Cloud Scheduler → authenticated `/api/v1/jobs/*` endpoints |
| Observability | Sentry free tier, JSON logs with `request_id` |
| CI | GitHub Actions running `scripts/verify.sh` lanes: `web`, `api`, `api-db`, `contract`, `infra` |

## Consequences

- One rule-owning service (FastAPI) makes tenancy, audit and AI permission checks enforceable in one place.
- Deferred until a measured trigger (PRD §3.2): Redis, a worker queue, WhatsApp/SMS, subscription billing, an own-domain email sender, Urdu RTL, pgvector, a separate AI service.
- Free-tier risks (PRD Appendix B): Vercel Hobby is non-commercial (move at the first paying clinic), Supabase free limits, Cloud Run cold starts (keep-warm during OPD hours), Gmail sending cap.
- At 10x load: add Redis for hot queue reads and rate limits, move the API to min-instances ≥ 1, and upgrade Supabase to Pro.
