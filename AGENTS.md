# Clinic Token & Queue SaaS — Agent Instructions

This repository is built with AI assistance under a strict, documented process. Read `context/` before doing anything else — it is the authoritative source for architecture, build sequencing, and conventions, and it wins over general knowledge or training-data defaults.

## Read First, In Order

1. `context/project-overview.md`
2. `context/architecture.md`
3. `context/code-standards.md`
4. `context/library-docs.md`
5. `context/ui-rules.md`
6. `context/ui-tokens.md`
7. `context/ui-registry.md`
8. `context/build-plan.md`
9. `context/progress-tracker.md`

## Source of Truth

- **Function, fields, screens, workflows, phases:** `docs/prd/PRD.md` wins (IDs F-, D-, R-, W-, I-, A-, Q-).
- **Technology and architecture:** `docs/adr/` wins, starting with `docs/adr/0001-stack-decision.md` (mirrors PRD §3).
- **How code is written:** `context/code-standards.md`. **Look and feel:** `context/ui-*.md`.
- **What to do next:** `context/build-plan.md`; **where we are:** `context/progress-tracker.md`.

Never invent a business field, rule or screen that is not in the source documents — record a change request in `docs/adr/` first.

## Non-Negotiable Constraints

- Multi-clinic SaaS: every tenant table has `clinic_id`; every query is scoped by the API and by RLS; cross-clinic access returns 404 (tested).
- Only the FastAPI service reads or writes the database. The browser uses Supabase only for Auth sessions and Realtime subscriptions.
- Business rules live in `apps/api/app/services`; routers and AI tools call services.
- The AI layer (`apps/api/app/ai`) holds no database credentials and runs no SQL; it calls approved tools with the caller's identity and clinic scope.
- Realtime payloads contain token numbers and counts only — never patient names or phones.
- Token numbers come from one transaction with a row lock on `token_counters`.
- Every token state change writes `token_events` + an audit row.
- Every schema change ships as an Alembic migration in the same PR.
- Patients never log in; they use an unguessable `/t/{public_code}` link. Staff log in by email magic link.
- Private visit `notes` are never shown to patients; `medicines_advice` only when the clinic setting and the visit checkbox allow it.
- Never add a field, screen or rule not in the PRD without a change request (PRD §25).

## Verification — How "Done" Is Decided

Verification is mechanical and automatic. Do not hand-pick test commands, start the app, or click through the UI to convince yourself a change works.

- **`scripts/verify.sh`** is the single definition of "verified". It runs only the lanes your changes affect (`web`, `api`, `api-db`, `contract`, `infra`) with the same commands CI runs. Default is the **fast tier** (format, lint, types, unit tests: seconds). `--slow` adds integration tests, builds, scans and drift checks; `--all` runs every lane with the slow tier; `--lane <name>` runs one; `--list` shows what would run. A fast PASS lists every slow check it deferred. Run `--slow` before you call a task finished.
- **Per edit** (Claude Code `PostToolUse` hook, `.claude/settings.json`): the edited file is formatted/lint-fixed in seconds; problems that cannot be auto-fixed are reported back immediately.
- **Per turn** (`Stop` hook): when you finish with uncommitted changes, the fast tier runs. If it fails you are not done: fix the reported failures. Never weaken, skip or delete a check to make it pass.
- **Checkpoints:** after each verified step, make a local commit on the task branch. A failed run returns to the last checkpoint instead of restarting. Never push without the developer's say.
- **Needs a human:** if verification cannot be trusted (an unreadable review verdict, a check you cannot run, a rule that conflicts with the task), stop and write the question under "Needs a human" in your reply and in `context/progress-tracker.md`. Do not guess.
- **When a run goes wrong,** name the failure class and fix the surface it lives on, per `HARNESS.md`. Then run `bash scripts/harness-check.sh`.
- **Per push** (`.githooks/pre-push`, enable once per clone with `bash scripts/install-hooks.sh`): the same lanes, for commits made outside an agent session.
- **Manual/browser checks** only for UI work, when the `review` skill calls for them.
- **E2E** (`.github/workflows/e2e.yml`, Playwright, full stack) is off the default PR path: add the `run-e2e` label to a PR that touches auth, sessions, API startup or the booking → NEXT → TV flow. It also runs on main and nightly.

Write tests for the behaviour the plan's **acceptance tests** name (see `architect`), plus the non-negotiable coverage in `context/code-standards.md`. Do not write tests for trivia.

**When CI fails on something `verify.sh` passed**, the fix PR carries two changes: the fix, and the check (a `verify.sh` step, an architecture test, or a lint rule) that would have caught it locally. CI should surprise us at most once per failure class.

## Skills

This repo's `skills/` directory defines the working process:

- `architect` — think through a feature before writing code; produces a plan with acceptance tests
- `imprint` — capture UI patterns into `context/ui-registry.md` after building a component
- `review` — verify a finished feature against the plan, the architecture, and production readiness
- `recover` — diagnose a failure (bug vs. polluted session vs. wrong approach) before responding to it
- `remember` — save/restore session state between sessions

## Current Status

See `context/progress-tracker.md` for the live phase/task status.
