# Code Standards

Implementation rules and conventions for Clinic Token & Queue SaaS. Follow these in every session without exception. These rules prevent pattern drift across sessions (Python API in `apps/api`, TypeScript web app in `apps/web`).

---

## Engineering Mindset

- **Think before implementing** — understand what is being built and why before writing a line
- **Read context files first** — never assume; verify against `architecture.md` and `project-overview.md`
- **Scope is sacred** — build only what the current task requires. Business fields not in the PRD require a change request
- **Every feature must be testable** — if it cannot be verified immediately after implementation, it is incomplete
- **Clean over clever** — readable code a junior developer can follow beats clever abstraction
- **One thing at a time** — complete one feature fully before touching the next
- **Reference the feature ID** — every task cites its feature/form ID or PRD section

---

## The Rules That Cannot Be Broken

These are architectural guarantees, not style preferences. A PR that violates one does not merge.
Each rule ends with `— enforced by: <check>`.

1. **No secrets in source control.** Ever. `.env.example` holds keys with empty values. — enforced by: secret scan (`security.yml`)
2. **No raw SQL string concatenation, anywhere.** Parameterized queries or the ORM only. — enforced by: ruff rule `S608` (string-built SQL) in the `api` lane + review
3. **`packages/api-client` is generated from the API contract, never hand-edited.** — enforced by: `verify.sh --lane contract` and the edit hook
4. **Every query is tenant-scoped.** Bypassing the scope filter requires an explicit comment justifying it and a reviewer's approval. — enforced by: architecture test that every tenant-owned entity is filtered + integration test
5. **No business logic in the frontend.** Calculation of price, tax, stock or totals happens in the backend only. The frontend formats and displays; it does not decide. — enforced by: review layer 2 + architecture rules
6. **The AI/agent service never gets a database connection string.** If a task seems to need one, the task is wrong. — enforced by: infrastructure network policy + `verify.sh` infra lane

7. **Only the API touches the database.** The browser uses the Supabase client for Auth sessions and Realtime subscriptions only; no `supabase.from(...)` data calls in `apps/web`. — enforced by: ESLint `no-restricted-syntax` rule on `.from(` in `apps/web` (`web` lane)
8. **Business rules live in `apps/api/app/services`.** Routers and AI tools call services and contain no rules; routers never import `app.models` directly. — enforced by: import-linter contract in the `api` lane
9. **Every endpoint declares a permission dependency.** — enforced by: architecture test that walks the FastAPI routes (`api` lane)
10. **Realtime payloads carry token numbers and counts only.** No patient name or phone ever goes into a broadcast. — enforced by: unit test on the realtime publisher schema (`api` lane)
11. **Token numbers are issued inside one transaction with a row lock on `token_counters`.** — enforced by: concurrency integration test (50 parallel bookings → 50 unique numbers) in the `api-db` lane
12. **Every token state change writes a `token_events` row and an audit row.** — enforced by: integration test per transition (`api-db` lane)
13. **Every schema change ships as an Alembic migration in the same PR.** — enforced by: `alembic check` in the `api-db` lane
14. **AI code in `apps/api/app/ai` never imports SQLAlchemy sessions or models.** It calls tools that call services with the caller's identity. — enforced by: import-linter contract in the `api` lane
15. **Private visit `notes` never reach a patient endpoint.** Only `medicines_advice` under W-011 rules. — enforced by: integration test on `/public/tokens/{code}/advice` (`api-db` lane)

---

## TypeScript / React / Next.js (`apps/web`)

- Strict mode; no exceptions
- Never `any` — use `unknown` and narrow; no `as X` assertions unless commented why
- Explicit parameter and return types on all functions
- `type` for object shapes and unions; `interface` only for extendable component props
- `const` by default
- (Next.js App Router) Server Components by default; `"use client"` only for state, effects, browser APIs or client-only libraries; never on a layout unless genuinely required
- Data fetching on the server; never fetch directly from a Client Component when a server path exists
- API types come from the generated client. Hand-written request/response types are a defect
- Schema validation (Zod) mirrors backend validation for UX only — the backend remains authoritative
- Currency, date and quantity formatting always goes through one `lib/format` module. Never inline `toLocaleString`
- Permission checks go through one `can(module, screen, action)` helper — unauthorized actions are hidden or disabled
- Every list view implements loading, empty, error and unauthorized states. All four, every time

## Python (`apps/api`)

- Python 3.12+; type hints on everything; `mypy --strict` in `verify.sh`
- Pydantic models for every input and output — no untyped dicts crossing a boundary
- `ruff` for lint and format; the edit hook runs `ruff --fix` on every touched file
- Timeouts on every outbound call
- Structured logging with a correlation/execution ID

---

## Naming

| Thing | Convention | Example |
| --- | --- | --- |
| Database tables | `lower_snake_case`, plural | `token_events` |
| Database columns | `lower_snake_case` | `visit_date`, `clinic_id` |
| Python modules / functions | `snake_case` | `services/queue.py`, `call_next()` |
| Python classes / Pydantic models | `PascalCase` | `TokenCreate`, `TokenOut` |
| TypeScript components | `PascalCase` file and export | `LiveQueueCard.tsx` |
| TypeScript hooks / utilities | `camelCase` | `useQueueChannel()` |
| Next.js routes | kebab-case folders | `app/(staff)/aaj-ki-list/page.tsx` |
| i18n keys | dotted, screen first | `liveQueue.peopleAhead` |
| Error codes | `UPPER_SNAKE_CASE` | `DAILY_LIMIT_REACHED` |
| Realtime channels | `queue:{clinic_id}:{doctor_id}` | `queue:7f…:a1…` |
| API routes | kebab-case, plural | `/api/v1/purchase-orders` |
| Branches | `type/short-description` | `feat/f-001-short-name` |

---

## Error Handling

- **Backend:** one global handler returns structured problem details (RFC 7807). Domain rule violations return 422 with the rule; permission failures 403; never leak stack traces or SQL to the client
- **Frontend:** every mutation surfaces success and error with an actionable message. Never a bare "Something went wrong"
- Sensitive data is masked in all logs

---

## Testing

| Level | Tool | Location | Lane / tier |
| --- | --- | --- | --- |
| Unit (domain rules, numbering, estimates, state machine) | pytest | `apps/api/tests/unit` | `api` fast |
| Architecture (imports, permission deps, tenant scope) | pytest + import-linter | `apps/api/tests/architecture` | `api` fast |
| Integration (API + Postgres + RLS + audit) | pytest + Postgres container | `apps/api/tests/integration` | `api-db` slow |
| Migrations | Alembic upgrade/check/downgrade | `apps/api/alembic` | `api-db` slow |
| Contract drift | openapi-typescript | `packages/api-client` | `contract` slow |
| Component / UI | Vitest + Testing Library + axe | `apps/web/**/*.test.tsx` | `web` fast |
| E2E | Playwright | `apps/web/e2e` | `e2e.yml` (label `run-e2e`, main, nightly) |

Non-negotiable test coverage (keep only what applies to this project):

- Every scoping rule — a user in scope A cannot reach scope B data through **any** endpoint
- Every audited action actually writes an audit row
- Every permission — the API rejects an unauthorized action even when the UI would have hidden it
- Every AI tool — authorization, data isolation, action safety, schema validation, audit

Prefer one architecture test covering every endpoint/entity over a hand-written test per feature for the same rule. A new "every X must Y" invariant belongs in the architecture tests; a deliberate exception goes in that test's exemption list with its reason.

### Verification loop

`scripts/verify.sh` is the local mirror of CI and the definition of "verified" (see `AGENTS.md` — Verification). Run it, or let the Claude Code hooks run it, instead of choosing commands by hand. A new CI check is added as a `verify.sh` lane step that the workflow calls, so local and CI cannot drift.

---

## Git & Pull Requests

- Protected `main`. No direct pushes
- One logical change per PR
- PR description records: the requirement (feature ID / PRD section), test evidence, and database migration notes
- Every PR is reviewed and understood by a human developer. AI-generated code is the author's responsibility, not the tool's
- CI must pass: `web`, `api`, `api-db`, `contract`, `infra` lane workflows (each runs `bash scripts/verify.sh --lane <name>`), `security.yml` (actionlint + gitleaks), `npm audit` on `web`; `e2e.yml` on the `run-e2e` label, on main and nightly
- When CI fails on something `verify.sh` passed, the fix PR carries two changes: the fix, and the check that would have caught it locally

---

## AI-Assisted Development Protocol

1. **Requirement** — a small, testable story with acceptance criteria
2. **Context** — supply the relevant structure, conventions and constraints. `context/` is that context
3. **Design** — agree database/API/UI design *before* large generation (`/architect`)
4. **Generate** — scaffolding, implementation, refactoring, tests
5. **Review** — a human reviews all generated code, queries, security and error handling (`/review`)
6. **Test** — the acceptance tests from step 1 were written first and pass; `scripts/verify.sh` passes
7. **PR** — requirement, test evidence, migration notes
8. **Merge** — only approved, passing PRs reach protected branches

AI tooling is never given unrestricted production credentials or unrestricted database write access. Production deployment uses controlled CI/CD credentials only.

All web source files must be saved as UTF-8. Run `node scripts/check-web-source-utf8.mjs` when changing files under `apps/web/src`; do not use a shell's legacy default encoding for source edits.
