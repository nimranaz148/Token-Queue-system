# Interview Question Bank

Used by the `prd` skill. Ask in **rounds**, 3-5 related questions per round. Skip anything the user already answered
(in their message, an existing PRD, the repo, or an earlier round). Every question offers a **recommendation first**, with a
one-line reason, then the alternatives. The user can always answer "you decide": pick the recommendation and record it in the
Assumptions ledger (PRD §0.3) so it is visible and can be challenged later.

After every round, replay a 3-6 line summary ("So far: …") and ask for corrections before moving on.

Tag legend: **[always]** ask every time · **[if X]** ask only when X is true (this is the "be intelligent" rule: do not ask about
Salesforce for a project with no customers, or about Redis before the user has said anything about load).

---

## Round 0 — Mode and seed idea [always]

1. Is there already a PRD/SOW/spec for this project? (path, link or paste) → **update mode** if yes (see `update-protocol.md`).
2. In 2-4 sentences: what are you building, for whom, and what problem does it remove?
3. Is there anything already built (repo, prototype, spreadsheet the business runs on today)? Should the PRD describe it or replace it?

## Round 1 — Ambition, budget and constraints [always]

This round decides the **profile**, which changes every later default (see `stacks.md` → Profiles).

1. **What is this for?**
   - *Prototype / demo* — prove the idea in days, throw away freely
   - *MVP* — real users, small scale, can be rebuilt in parts
   - *Production* — paying customers, uptime and data-integrity matter (recommend when money, personal data or other companies' data are involved)
   - *Enterprise / regulated* — audit, compliance, SSO, formal change control
2. **Budget for running costs?**
   - *Free tiers and open source only* (say which free tiers you accept: Supabase, Vercel, Neon, Fly, Cloudflare…)
   - *Low* (a few tens of USD/month)
   - *Comfortable* (managed services are fine when they save engineering time)
   - *Not a constraint*
3. **Team and timeline:** how many developers, which languages do they already know well, and by when must something usable exist?
4. **Hosting constraints:** cloud, self-hosted VPS, on-premise, or hybrid? Any data-residency rule (data must stay in a country)?
5. **Licensing:** must the whole stack be open source / permissively licensed? Any vendor you must use or must avoid?

## Round 2 — Users, scale and shape of the product [always]

Numbers here size the stack, the phases and the page count. If the user does not know, offer the ranges below and record the pick.

1. **Who uses it?** List each user type/role and what each one mainly does (e.g. operator, branch manager, accountant, customer).
2. **How many users?** Total accounts and peak concurrent users. Ranges: `<50` · `50-500` · `500-5,000` · `5,000+`.
3. **Tenancy:** one company only, several companies (SaaS, data must be isolated per tenant), or several branches/locations inside one company? → drives `tenancy` in the harness.
4. **Data volume:** rows per main entity after a year (`<10k` · `10k-1M` · `1M-100M` · more) and file/attachment volume.
5. **How many frontend pages/screens?** Ranges: *5-10 (prototype)* · *10-30 (MVP)* · *30-80 (typical business app)* · *80+ (large multi-module platform)*. Ask which are list pages, forms, dashboards, and any special screens (checkout, kanban, calendar, map, editor).
6. **Devices and channels:** desktop web, mobile web, native mobile app, tablet/touch kiosk, public API for partners?
7. **Languages, currencies, time zones, accessibility level** (WCAG AA is the default recommendation for anything public).

## Round 3 — Domain, features and phases [always]

1. **Modules:** propose a module list based on the seed idea and let the user add/remove. For each module ask: which workflows matter most?
2. **Priorities:** for every module, classify P0 (must be in first release), P1 (commercial release), P2 (expansion), P3 (differentiation). Keep P0 small and honest.
3. **Reports and dashboards:** which numbers does the owner look at every day? Every KPI should drill down to a list of records.
4. **Documents and money [if it handles money or stock]:** are there documents that get *posted* (invoices, stock movements, journal entries) and must never be edited afterwards, only reversed? Which currency precision and rounding rules?
5. **Audit [if more than one user role]:** which actions must leave an audit trail (discounts, deletions, permission changes, exports)?
6. **Offline [if the product is used in shops, warehouses, field work]:** must it keep working without internet? For how long? What happens on conflict?
7. **Compliance [ask, then follow up only on "yes"]:** tax/e-invoicing authority integration, GDPR/UAE/PK/… privacy law, PCI (card data), HIPAA (health), SOC 2, industry-specific rules.
8. **Phases:** propose a phase count from scope and team size (rule of thumb: prototype 1, MVP 2-3, production 4-6, enterprise 6-8, with **Phase 0 = foundation** always first). Ask whether the user wants a different number and what each phase's *exit test* should be.

## Round 4 — Stack preferences and recommendation [always]

1. **Do you already have a preferred stack?** Show the presets in `stacks.md` (Preset A is the default when the team is Python-friendly). If they name a stack, respect it and only flag genuine mismatches.
2. If they have none or ask for advice: **give one clear recommendation** based on Round 1-3 answers and explain it in 4-6 lines (why this fits, what it costs, what you would change if a number in Round 2 turns out 10x bigger). Mention one alternative at most.
3. **Frontend:** framework (Next.js / React+Vite / SvelteKit / Nuxt / Blazor / Angular / server-rendered templates), UI kit (shadcn/ui, Radix, MUI, Ant Design, Mantine, Bootstrap), styling (Tailwind v4, CSS modules), forms/validation, data tables, charts, state/data fetching.
4. **Backend:** language/framework (FastAPI, Django, NestJS/Express, ASP.NET Core, Spring Boot, Go with chi/gin/fiber, Rails, Laravel), API style (REST + OpenAPI, GraphQL, tRPC, gRPC), and whether the frontend talks to the backend directly or through a BFF.
5. **Database and migrations:** Postgres (plain, Supabase, Neon, RDS), MySQL, SQL Server, SQLite (prototype only), plus ORM/migration tool (SQLAlchemy + Alembic, Prisma, Drizzle, EF Core, Flyway/Liquibase, Django ORM). Recommend Postgres unless a constraint says otherwise.
6. **Repo shape:** single repo/monorepo (recommended), folders (`apps/api`, `apps/web`, `apps/agents`, `packages/*`), package manager (npm/pnpm/uv/poetry).

## Round 5 — Platform services (ask only what is relevant) [mostly conditional]

For each item, state the default you would use and why. Ask about an item only when its trigger is true.

| Service | Ask when | Default recommendation |
| --- | --- | --- |
| Authentication | there are users [always] | Prototype/MVP on Supabase: Supabase Auth. Own backend: short-lived JWT + httpOnly refresh cookie. Enterprise: Keycloak/Entra ID/Okta (OIDC). MFA: yes for admin roles |
| Authorization | more than one role | Role → permission matrix enforced **in the API**; UI only hides |
| **Redis / cache** | user mentions rate limits, queues, sessions, live dashboards, hot reads, or expects > ~500 concurrent users | **Do not add by default.** Start with Postgres (`UNLOGGED` tables / advisory locks / `LISTEN`), add Redis when a measured need appears; then Valkey/Redis for rate limiting, cache, pub/sub |
| Background jobs / queues | emails, imports/exports, reports, webhooks, AI runs, scheduled work | Python: arq or Celery (+ Redis) · Node: BullMQ · .NET: Hangfire/Quartz · Go: River (Postgres) · Simple: Postgres-backed queue; durable workflows: Temporal |
| Search | large catalogs, fuzzy/typo-tolerant search | Postgres `pg_trgm` + FTS first; Meilisearch or Typesense when relevance matters; OpenSearch only at scale |
| File/object storage | uploads, images, PDFs, exports | S3-compatible: Supabase Storage / Cloudflare R2 / S3 / MinIO (self-host) |
| Realtime | live dashboards, queue/status screens, chat, collaboration | SSE first; WebSocket when bi-directional; Supabase Realtime if already on Supabase |
| Email / SMS / push | notifications, receipts, password reset | Resend/Postmark/SES · Twilio/local SMS gateway · web push |
| Payments | the product takes money | Stripe (global) or a local gateway; card data never touches your servers |
| PDF / documents | invoices, reports | WeasyPrint/Puppeteer/Playwright print, or a report service |
| Observability | production or enterprise profile | OpenTelemetry + Sentry; Grafana/Loki/Prometheus or a managed APM; structured logs with correlation ID |
| Secrets / config | always | `.env.example` with empty values; a secret manager in production |
| Feature flags / A-B | staged rollout wanted | Start with config flags; Unleash/GrowthBook/PostHog if needed |
| Product analytics | growth product | PostHog (self-hostable) |
| CI/CD and hosting | always | GitHub Actions; hosting per Round 1 (Vercel + Fly/Render/Railway, AWS/GCP/Azure, VPS + Docker Compose, Kubernetes for enterprise) |
| Containers | always | Docker + Compose for local and CI parity |
| Backups and DR | production/enterprise | Managed Postgres PITR or scheduled `pg_dump`; a **restore test** scheduled in CI |

## Round 6 — AI features [ask "will AI be part of the product?" always; the rest only on "yes"]

1. Which jobs should AI do (answer questions over data, draft documents, classify, forecast, automate back-office tasks, chat assistant)?
2. **Agent framework:** OpenAI Agents SDK (recommended when the user already uses it), Claude Agent SDK, LangGraph, Pydantic AI, Vercel AI SDK, Mastra, or plain function calling.
3. **Models/providers** and whether any data may leave the company (else: local models via Ollama/vLLM).
4. **Autonomy level** per agent: L1 explain · L2 recommend · L3 draft (needs approval) · L4 act within limits · L5 fully autonomous. Recommend L1-L3 for the first release.
5. **Guardrails:** the AI never gets database credentials; it calls approved tools that go through the same API and permission checks as a human user; every tool call carries the caller's identity and is audited.
6. Vector search/RAG (pgvector first), evaluation set, cost limit per tenant, prompt-injection handling.

## Round 7 — Integrations [conditional, be selective]

Ask only about integrations that the domain implies.

| Ask about | Only when |
| --- | --- |
| **CRM (Salesforce, HubSpot, Zoho)** | the product has customers/leads/sales pipeline **and** the company already runs a CRM or wants to sync contacts/deals. Otherwise: "your own customer module is enough for now" |
| Accounting (QuickBooks, Xero, Odoo, local tools) | invoicing, payments or financial reports exist and someone else keeps the books |
| Back-office systems (ERP, HR, payroll) | the product is meant to feed or replace one |
| Payment gateways, bank feeds | money moves |
| Shipping/couriers, marketplaces, e-commerce (Shopify, WooCommerce) | physical goods are sold or delivered |
| Government / tax / e-invoicing | Round 3 compliance answer was "yes" (treat as P0, never defer) |
| Hardware (printers, scanners, scales, card terminals, cash drawers) | in-person selling or warehouse work |
| Webhooks / public API for partners | Round 2 channel answer included partners |
| SSO / directory (Google Workspace, Entra ID) | company staff log in |
| Import/migration from an existing system | Round 0 said something exists today |

## Round 7b — Look, feel and motion [only if the product has a web UI]

Ask these as recommendations, not a survey. The answers feed `/uiux` and PRD §16.

1. **Motion level.** Recommend by product type: marketing / brand / portfolio site → `cinematic 3D` (animated, scroll-driven, 3D-forward, GSAP-class motion, production-grade from the first build); typical product or content site → `refined motion`; admin panel, dashboard, internal tool → `minimal` (heavy motion slows people down). The user decides. Record it as `motion: cinematic | refined | minimal` in PRD §16 and the discovery log.
2. **Palette direction.** Propose a distinctive palette from the brand and industry (mood in three words, one accent, light or dark leaning) and ask for confirmation or a change. Never default to a generic SaaS look.
3. **Type direction.** Editorial display face plus readable body face, free for commercial use unless the budget says otherwise. Ask only if the user has brand fonts.
4. **References.** Ask for up to three sites they admire (for the inspiration research); say that the GSAP Showcase is the default source of award-calibre examples.
5. **Skills.** Say that the UI skill set can be installed (recommended for any website) and that `/uiux` will use whichever is installed.

## Round 8 — Non-functional and delivery [always, short]

1. Performance targets (e.g. "search results < 300 ms", "checkout < 1 s"), uptime target, acceptable downtime window.
2. Security level: data classification, encryption at rest, pen-test, audit-log retention.
3. Backup/DR: RPO/RTO the business can live with.
4. Testing depth: unit + integration always; E2E on critical flows; performance tests for hot paths; how many UAT users?
5. Deliverables beyond code (admin manual, user manual, ERD, API docs, deployment guide, training).
6. Who approves the PRD and each phase gate?

---

## After the last round

1. Present the **Decision Summary** (profile, stack table, phases, page estimate, P0 list, services chosen and *not* chosen, assumptions).
2. Ask: "Anything to change before I write the PRD?"
3. Only then write the document (see SKILL.md → Step 5).

## Style rules for the interviewer

- Never ask more than five questions at once. Number them.
- Never ask something you can answer by reading the repo or the user's earlier text.
- Put the recommendation first and mark it **(Recommended)**.
- If the user is unsure, explain the trade-off in two sentences, then recommend.
- Do not lecture. Do not list every tool in the ecosystem; show 2-4 options that fit the profile.
- Never invent numbers the user did not give; ranges are offered, the choice is theirs.
