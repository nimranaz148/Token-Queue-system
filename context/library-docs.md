# Library Docs

Project-specific usage patterns for every third-party library in this project. This file covers how *we* use each library in Clinic Token & Queue SaaS — rules, patterns and constraints specific to this project. It is not a substitute for the official docs.

---

## Before Using Any Library

1. **Check `AGENTS.md`** at the project root for installed skills.
2. **Fetch current API documentation** (Context7 MCP or the official docs) — library APIs change and training data goes stale. This is required, not optional, for any library question.
3. **Read this file** for project-specific patterns that override general library knowledge.

Order of authority:

```
Current official docs -> Skills via AGENTS.md -> This file (project rules) -> General knowledge
```

---

## Adding a library

When a task adopts a new library, add a section here **in the same PR** using this shape:

```
## <Library> (<package name>, <pinned version>)

Where it is configured: <file>
Project rules:
- <the pattern we always use>
- <the thing we never do, and why>
Gotchas found in this project:
- <symptom> -> <cause> -> <fix>
```

## Next.js (App Router) — `apps/web`
- **Used for:** all screens: public booking/token pages, staff screens, TV display.
- **Our rules:** public pages (`/c/[slug]`, `/t/[code]`) server-render the first numbers; Realtime only in client islands. No data calls to Supabase from the browser.
- **Docs:** https://nextjs.org/docs

## Tailwind CSS v4 + shadcn/ui — `apps/web`
- **Used for:** styling and components; tokens from `context/ui-tokens.md` only.
- **Docs:** https://tailwindcss.com/docs · https://ui.shadcn.com/docs

## React Hook Form + Zod — `apps/web`
- **Used for:** every form; Zod schemas mirror the API's Pydantic rules (PRD §5.3).
- **Docs:** https://react-hook-form.com · https://zod.dev

## TanStack Query — `apps/web`
- **Used for:** server state; Realtime events invalidate queue queries.
- **Docs:** https://tanstack.com/query/latest

## next-intl — `apps/web`
- **Used for:** English + Roman Urdu strings (`messages/en.json`, `messages/roman-ur.json`).
- **Docs:** https://next-intl.dev

## Recharts — `apps/web`
- **Used for:** D-001 7-day chart and other dashboards (bar and line only).
- **Docs:** https://recharts.org

## FastAPI + Pydantic v2 — `apps/api`
- **Used for:** the only API; OpenAPI at `/openapi.json`; health at `/api/v1/health`.
- **Our rules:** routers → services → models; errors as RFC 7807 with a `code`.
- **Docs:** https://fastapi.tiangolo.com · https://docs.pydantic.dev

## SQLAlchemy 2 (async) + Alembic — `apps/api`
- **Used for:** data access and migrations; `ScopedSession` adds `clinic_id` scope; RLS policies live in migrations.
- **Docs:** https://docs.sqlalchemy.org/en/20/ · https://alembic.sqlalchemy.org

## Supabase (Postgres, Auth, Realtime, Storage)
- **Used for:** database; staff email magic-link login (custom SMTP, Gmail app password); Realtime broadcast published by the API; private storage buckets.
- **Our rules:** service-role key only in the API runtime; API verifies JWTs via JWKS.
- **Docs:** https://supabase.com/docs

## Cloudflare Turnstile
- **Used for:** anti-bot check on public booking (F-001), verified server-side.
- **Docs:** https://developers.cloudflare.com/turnstile/

## OpenRouter (`openai` Python SDK) + Google Gemini (`google-genai`) — `apps/api/app/ai`
- **Used for:** Phase 4 AI features behind one provider interface; Gemini is the fallback.
- **Docs:** https://openrouter.ai/docs · https://ai.google.dev/gemini-api/docs

## openapi-typescript — `packages/api-client`
- **Used for:** generating `src/generated/schema.ts` from the API contract.
- **Docs:** https://openapi-ts.dev

## Playwright, Vitest, pytest
- **Used for:** E2E, web unit/component and API tests (see `context/code-standards.md` → Testing).
- **Docs:** https://playwright.dev · https://vitest.dev · https://docs.pytest.org

## Sentry
- **Used for:** error monitoring in web and API, with PII scrubbing.
- **Docs:** https://docs.sentry.io
