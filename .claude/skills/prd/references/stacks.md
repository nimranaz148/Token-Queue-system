# Stack Catalog and Recommendation Rules

Used by the `prd` skill (Round 4-5) and read by `bootstrap` when it picks lanes. Keep recommendations short and justified.
Versions drift: before writing a version number into a PRD, check the tool's current documentation.

## Profiles (from Round 1)

| Profile | Optimise for | Defaults |
| --- | --- | --- |
| **Prototype** | Speed to a clickable/demo-able thing; cost ≈ 0 | One repo, SQLite or Supabase free tier, no queues, no Redis, minimal auth, no offline, E2E optional, 1 phase |
| **MVP** | Real users, small scale, fast iteration | Postgres, migrations from day one, auth + roles, CI with lint/tests, Docker Compose, 2-3 phases |
| **Production** | Correctness, uptime, security | Everything in MVP plus: audit log, tenancy rules, architecture tests, integration tests on a real DB, backups with a restore test, observability, rate limits, secret manager, 4-6 phases |
| **Enterprise / regulated** | Governance, compliance | Everything in Production plus: SSO/OIDC, MFA, formal change control, data-retention rules, pen-test, DR drills, separate environments, 6-8 phases |

## Presets

Recommend a preset, do not just list them. State what changes at 10x scale.

### Preset A — "Python API + Next.js"
- **Frontend:** Next.js (App Router, TypeScript strict), Tailwind CSS v4, shadcn/ui, React Hook Form + Zod, TanStack Table, Recharts
- **Backend:** FastAPI (Pydantic v2), SQLAlchemy 2 + **Alembic** migrations, `uv` for Python packages, ruff + mypy + pytest
- **Database:** PostgreSQL (Supabase for MVP; plain Postgres/Neon/RDS for production), Docker Compose locally
- **AI:** OpenAI Agents SDK in a separate service that reaches data only through the API's tools
- **Contract:** OpenAPI from FastAPI → generated TypeScript client (`openapi-typescript`) → drift check in `verify.sh`
- **Harness lanes:** `web` (node), `api` (python), `api-db` (alembic), `contract`, `infra`
- **Pick when:** small team, fast delivery, AI features, Python skills in the team. **Watch:** async/sync mixing in SQLAlchemy; multi-tenant filtering must be enforced centrally (dependency/session scoping + a test).

### Preset B — ".NET enterprise"
- ASP.NET Core Web API (Clean Architecture), EF Core + Npgsql or SQL Server, Next.js or Blazor frontend, xUnit + Testcontainers, OpenAPI client generation
- **Harness lanes:** `dotnet`, `dotnet-db`, `contract`, `node`, `infra`
- **Pick when:** Microsoft shop, strong typing/long-lived enterprise code, existing .NET team. Heavier start, excellent tooling and performance.

### Preset C — "TypeScript everywhere (MERN/T3-style)"
- Next.js or React+Vite, Node (NestJS/Express/Fastify) or Next route handlers, Prisma/Drizzle on Postgres (Mongo only if the data is truly document-shaped), tRPC or REST+OpenAPI
- **Harness lanes:** `node` (one per package), `infra`
- **Pick when:** JS/TS-only team, one language end to end. **Watch:** business logic leaking into route handlers; keep a domain layer.

### Preset D — "Go service"
- Go (chi/gin/fiber or stdlib), sqlc/pgx, goose/atlas migrations, React/Next frontend
- **Harness lanes:** `go`, `node`, `infra`
- **Pick when:** high throughput, low memory, simple deployment (single binary), infrastructure/tooling products.

### Preset E — "Java/Kotlin Spring Boot"
- Spring Boot 3, JPA/jOOQ, Flyway/Liquibase, React/Angular frontend
- **Pick when:** bank/enterprise Java shop. (No first-class harness lane yet: write a custom lane, see `docs/extending.md`.)

### Preset F — "Django full-stack"
- Django + DRF or HTMX/templates, Django ORM migrations, Celery
- **Pick when:** admin-heavy CRUD apps, content sites, very fast MVPs by Python developers. Use the `python` lane plus a custom `manage.py check`/`makemigrations --check` step.

### Preset G — "Prototype in a weekend"
- Next.js + Supabase (Auth, Postgres, Storage) + Vercel, or SvelteKit + SQLite, no separate API, no queues.
- **Pick when:** profile is Prototype. Write down what gets thrown away when it becomes an MVP.

## Recommendation rules (apply in order)

1. **Respect the user's stated stack.** Only warn about a real conflict (e.g. "SQLite plus 500 concurrent writers").
2. **Match the team's language** before chasing the "best" tool. A slightly worse tool everyone knows beats a better tool nobody does.
3. **Profile sets the floor:** Production/Enterprise always get migrations, tests on a real database, audit, backups, CI.
4. **Postgres by default.** Choose something else only for a stated reason (SQL Server mandate, embedded/offline device, prototype).
5. **Monolith first.** One API service + one web app. Add a separate service (agents, workers, realtime) only when its isolation is a requirement (AI must not touch the database; long jobs; different scaling).
6. **Add infrastructure on evidence.** Redis, queues, search engines, Kubernetes, microservices: each needs a sentence in the PRD saying which requirement forces it. If none, list it under "Considered and deferred".
7. **Open source and free-tier fit:** when the budget is "free only", prefer self-hostable OSS (Postgres, MinIO, Meilisearch, PostHog, Keycloak, Grafana stack) and free tiers with clear limits (Supabase, Vercel hobby, Neon, Cloudflare R2); write the limits into the PRD's risk list.
8. **State the exit ramp:** one line on how the choice changes if load or team grows 10x.

## Page and phase estimation heuristics

Use only as a starting point; the user decides.

| Product size | Frontend pages | Phases | Typical modules |
| --- | --- | --- | --- |
| Prototype | 5-10 | 1 | 1-2 |
| Small business tool (MVP) | 10-30 | 2-3 | 3-5 |
| Line-of-business app | 30-80 | 4-6 | 6-10 |
| Large multi-module platform | 80-200+ | 6-8 | 10+ |

- Count list + create/edit form + detail as separate pages for each master entity (≈ 2-3 pages per master).
- Dashboards: 1 per role that reads numbers daily.
- Phase 0 is always **foundation**: repo, CI, migrations, auth, tenancy/audit skeleton, design tokens, one vertical slice.
- Give every phase an **exit test** a person can run ("a user completes the core transaction end to end").

## Harness lane mapping (what `bootstrap` will generate)

| Chosen tech | Lane snippet |
| --- | --- |
| Next.js/React/Node package | `node` (one lane per package folder) |
| FastAPI/Python + uv + ruff + mypy + pytest | `python` |
| Alembic migrations against Postgres | `alembic` |
| ASP.NET Core / xUnit | `dotnet`, `dotnet-db` |
| Go | `go` |
| OpenAPI → generated client | `contract` |
| Docker Compose, GitHub Actions | `infra` |
| Anything else | custom lane written by `bootstrap` in the same shape |

## Stack to skill tags

Tags the `prd` skill resolves against `skills-manifest.json` after the stack is confirmed. A tag with no manifest entry is reported, never invented.

| Stack or need | Tags |
| --- | --- |
| Any website | `ui-core`, `typography`, `color`, `layout`, `accessibility`, `performance` |
| Marketing / brand site, cinematic motion | `gsap`, `scrolltrigger`, `cinematic-scroll`, `three-3d`, `anti-slop` |
| Next.js | `nextjs`, `tailwind`, `react-patterns` |
| Python API | `fastapi`, `pytest`, `sqlalchemy-alembic` |
| .NET API | `dotnet-api`, `efcore` |
| Node API | `node-api`, `testing-node` |
| Postgres | `postgres` |
| Auth provider (Clerk, Auth0, NextAuth) | `auth-<provider>` |
| Payments (Stripe) | `payments-stripe` |
| AI agents | `agents-sdk`, `agent-evals` |
| DevOps / infra | `docker`, `ci-github-actions`, `iac` |
| Vendor integration (Salesforce, Upwork, ...) | `integration-<vendor>` (project-local if no upstream skill) |
