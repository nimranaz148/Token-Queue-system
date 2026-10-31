---
name: bootstrap
description: Turn a PRD into a spec-driven Claude Code project setup - AGENTS.md, context/ docs, the five process skills (architect, imprint, review, recover, remember), scripts/verify.sh with per-stack lanes, edit/stop/pre-push hooks, CI workflows and an ERD generator. Use when the user runs /bootstrap <prd-path> or asks to set up the spec-driven workflow for a new project.
---

You are setting up a project so that every later Claude Code session follows the same documented process: read the spec docs, plan with acceptance tests, build, and let machines decide "done".

Everything you need ships with this skill. **Locate `HARNESS`** (the folder that contains `templates/` and `skills/`) in this order, and use it as `$HARNESS` below:

1. `harness/` next to this `SKILL.md` (installed or zipped copy; this is the normal case outside Claude Code plugins)
2. `${CLAUDE_PLUGIN_ROOT}` (Claude Code plugin install)
3. the checkout path the user gives you (ask once if 1 and 2 do not exist)

Templates live in `$HARNESS/templates/`. Never write outside the target project.
This skill runs in any agent that loads `SKILL.md` skills and can run shell commands (Claude Code, Codex CLI, Gemini CLI, OpenCode, Cursor, Antigravity). Where it says "ask the user", use a structured question tool if you have one, otherwise plain numbered questions.

## Rules

- **Nothing is written before the user confirms the summary in Step 4.**
- **Never overwrite an existing file.** If a target path exists, show what would change and ask; default is skip.
- **Never invent product facts.** Anything the PRD does not answer goes into `context/progress-tracker.md` under Open Questions.
- **Do not generate application code or scaffold the app** (no `dotnet new`, `create-next-app`). This sets up the process only.

## Step 1 — Read the PRD

Argument is the PRD path (`.md`, `.txt`, `.docx`, `.pdf`). If it is not Markdown, convert it first: `python3 $HARNESS/tools/read_spec.py <file> --out docs/prd/PRD.md` (or `$HARNESS/skills/prd/scripts/read_spec.py` in the plugin layout). Exit code 3 means no PDF extractor is installed: read the PDF yourself or ask for a `.docx`/`.md`. A PRD that did not come from the `prd` skill may lack the standard sections: say so and offer to run the `prd` skill in update mode first. If missing, look for `docs/prd/PRD.md`; if there is none, tell the user to run the `prd` skill first (it interviews them and writes one) and stop. Read it fully.

**If the PRD starts with YAML front matter** (written by the `prd` skill), take `project`, `slug`, `profile`, `stack`, `features`, `layout` and `phases` from it as already-confirmed answers: skip Step 3's questions, use `layout` for the folder paths, use §3.1 for the stack, §22 for phases, §26 for priorities and §3.7 for the non-negotiable constraints. Otherwise extract:

- Product name, users, problem, objectives
- Modules / screens / feature IDs (use the PRD's own IDs; if none, create `F-001…` in PRD order)
- Phases and exit criteria (if none, propose Phase 0 foundation + one phase per major module group)
- Hard constraints: multi-tenancy, permissions/roles, audit, offline, compliance, AI/agents, data residency, performance targets
- Stack hints and whether it has: a UI, a relational database, an API contract (OpenAPI/GraphQL), AI agents

## Step 2 — Inspect the target repo

Run in the current working directory (the target project). Note: is it a git repo, what folders exist, is there already an `AGENTS.md`, `context/`, `scripts/verify.sh`, `.claude/settings.json`? Detect existing manifests (`*.sln`, `package.json`, `pyproject.toml`, `go.mod`) to infer stack and folder layout. If `git` is not initialised, ask before running `git init`.

## Step 3 — Decide the stack and lanes

Infer from the PRD and repo. Ask at most 3 questions (backend, frontend, database) and only for what is still unknown, offering a recommendation with each. Then choose lanes — one per independently-verifiable folder:

| Lane snippet | Use for | Vars |
|---|---|---|
| `dotnet` | .NET solution: format, build, tests, NuGet vulnerability scan | `DIR`, `SLN`, `TESTS` (space-separated test project folder names under `DIR/tests`) |
| `dotnet-db` | EF Core: model matches latest migration + Testcontainers integration tests. Use when the .NET project has a database | `DIR`, `NS`, `MIGRATIONS_DIR`, `SNAPSHOT`, `EF_PROJECT`, `EF_STARTUP` |
| `contract` | Generated API client must match the live OpenAPI contract. Use when the project has a generated client package | `DIR`, `CLIENT_DIR`, `START_CMD` (may use `$PORT`), `PORT`, `HEALTH_PATH`, `SPEC_PATH`, `GEN_CMD` (may use `$SPEC_URL`), `GENERATED_FILE` |
| `node` | Next/React/Node package: lint, typecheck, test, build (reuse for several packages, one lane each) | `DIR` |
| `python` | uv + ruff + mypy + pytest | `DIR` |
| `alembic` | Alembic migrations apply to an empty Postgres, match the SQLAlchemy models (`alembic check`) and round-trip. Use with a FastAPI/SQLAlchemy project | `DIR`, `URL_ENV` (e.g. `DATABASE_URL`), `PG_IMAGE` (e.g. `postgres:16`) |
| `go` | Go module: gofmt, vet, test | `DIR` |
| `infra` | docker compose config + actionlint + verify.sh syntax | `INFRA_DIR` |

Lane var values must not contain `;`. Use the lane name you want in the `--lane 'name=snippet@…'` argument (e.g. `api=dotnet`, `api-db=dotnet-db`, `web=node`).

If the stack is not covered, write a new snippet in the target's `scripts/verify.sh` following the same shape (a `lane_<name>()` function using `step`, a `touched` regex, and the format-hook case), and tell the user it is custom. Always include `infra` when the repo will have CI workflows or Docker.

Pick the folder layout now (e.g. `apps/api`, `apps/web`) — these paths are used by lanes, `architecture.md` and CI, so they must be identical everywhere.

## Step 4 — Confirm

Present one short summary and wait for an explicit yes:

```
Blueprint ready.

Project: <name>            Stack: <backend> + <frontend> + <db>
Lanes:   <lane=snippet@DIR>, ...
Phases:  <phase list, one line each>
UI files: yes/no           ERD tooling: yes/no
Non-negotiables (from the PRD):
- ...
Open questions (PRD is silent): ...
Existing files that will be skipped: ...

Context files to generate (default: all four):
  project-overview.md · architecture.md · build-plan.md · progress-tracker.md
Foundation tasks in Phase 0 (default set from the PRD features): adr, scaffold, ci, database, auth, tenancy, audit, contract, ui, agents, slice
```

Then ask: **"Anything to add or remove?"** The defaults suit most projects; the user may drop files, drop foundation tasks (`--skip-task`), add tasks (`--phase0-extra`), turn off the mock-data-first principle (`--no-mock-first`), or ask for different stack lanes or extra docs. Apply their answers in Step 5.

## Step 5 — Generate

Work in this order. Use `{{PLACEHOLDER}}` substitution only from confirmed facts.

1. **Assemble the verification tooling** (deterministic — do not hand-write these):
   ```
   bash "$HARNESS/templates/scripts/assemble.sh" --target . \
     --lane '<name>=<snippet>@KEY=VAL;KEY=VAL' ... \
     [--generated-guard '<glob>|<message>']   # only if the project has generated code (e.g. an API client)
   ```
   This writes `scripts/verify.sh`, `scripts/hooks/format-on-edit.sh`, `scripts/hooks/verify-on-stop.sh`, `scripts/install-hooks.sh`, `scripts/check_verdict.py` and `scripts/harness-check.sh`.
2. Copy `templates/.claude/settings.json`, `templates/.githooks/pre-push`. Add `.claude/settings.json` only if absent; if present, merge the two hooks and show the diff. Also copy `templates/HARNESS.md` to `HARNESS.md` (never overwrite an existing one). When merging into an existing `.claude/settings.json`, keep the project's own rules and add the `permissions.deny` / `permissions.ask` entries; then run `bash scripts/harness-check.sh` and report its result.
3. **CI** (`.github/`):
   - For each lane, copy `workflows/lane.yml.tmpl` to `.github/workflows/<lane>.yml`, set `{{LANE}}` and `{{LANE_PATH}}`, and replace the `{{SETUP_STEPS}}` comment with the toolchain setup step (setup-dotnet / setup-node / astral-sh/setup-uv / setup-go). The workflow must call `bash scripts/verify.sh --lane <name>` — never duplicate the commands. Node lanes also get a `npm audit --audit-level=high` job; `dotnet` lanes already scan NuGet inside the lane.
   - Always copy `workflows/security.yml` as is (actionlint + gitleaks secret scan).
   - If the PRD has a web UI, copy `workflows/e2e.yml.tmpl` to `.github/workflows/e2e.yml` and fill `{{PREPARE_ENV_STEP}}`, `{{START_STACK_CMD}}`, `{{HEALTH_URLS}}`, `{{BASE_URL}}`, `{{WEB_DIR}}`, `{{INFRA_DIR}}`. E2E stays off the default PR path (label `run-e2e`, merge to main, nightly). Mention the `run-e2e` label in `AGENTS.md` → Verification.
   - Render `dependabot.yml.tmpl` (see the render step below) with `--ecosystem` set to the ecosystems in use.
4. **Skills**: copy `$HARNESS/skills/{architect,imprint,review,recover,remember}` into the project's `skills/`. If the PRD has a web UI, tell the user to run the `uiux` skill next (design system and page documents at the motion level chosen in the PRD) before building any page. If the project has no UI, still copy `imprint` but note in `AGENTS.md` that it is unused until UI exists.
5. **Context docs** in `context/`.
   - **Generated from the PRD by a script** (deterministic, so these files always get created): 
     ```
     python3 "$HARNESS/templates/scripts/context_from_prd.py" docs/prd/PRD.md --out context        [--files overview,architecture,build-plan,progress-tracker,progress-log] [--packs web-app,backend-api] [--skip-task audit] [--phase0-extra "task text"] [--no-mock-first]
     ```
     This writes `project-overview.md`, `architecture.md`, `build-plan.md` (phase map, Phase 0 foundation tasks derived from the PRD `features`, then one task per form/dashboard/integration in the registers, IDs preserved) and `progress-tracker.md` (one checklist per phase, PRD §0.4 open questions copied in). It never overwrites an existing file unless `--force`. Read its warnings (empty sections, phases without items) and fix them in the PRD or by hand. Every task carries `Acceptance:` lines; the plan states the task-size rule and the production-MVP infrastructure ladder; `progress-tracker.md` stays short and history goes to the append-only `progress-log.md`. With `--packs` (take the list from the PRD front matter `packs:` or `python3 "$HARNESS/scripts/packs.py" detect docs/prd/PRD.md`) it also adds each pack's Phase 0/1 tasks, its checklist as gates to answer before Phase 1 exits, and its deferred items with their triggers. Run `python3 scripts/check_plan.py` after editing the plan: it flags duplicates, tasks without acceptance criteria, oversized tasks and a tracker that disagrees with the plan. After it runs, **read the three files** and improve wording or add tasks the script cannot know; they are living documents.
   - **Rendered from full templates** with the deterministic renderer, then completed by you:
     ```
     python3 "$HARNESS/templates/scripts/render.py" <template> <out> \
       --stack dotnet,typescript --when tenancy,audit,money,ui --optional touch,dashboards \
       --var PROJECT_NAME=... --var API_DIR=... --var WEB_DIR=...
     ```
     `--stack` values: `dotnet`, `typescript`, `python`, `go`. `--when` values: `tenancy`, `audit`, `money`, `ai-agents`, `api-contract`, `database`, `ui`, `posted-documents` (pass only those the PRD actually has). `--optional` values (UI files): `touch` (touch-first / kiosk screens), `dashboards`, `ai`. The renderer prints any `{{PLACEHOLDER}}` still unfilled — fill each by editing the output file (e.g. `{{PROJECT_RULES}}`, `{{NAMING_TABLE}}`, `{{TESTING_TABLE}}`, `{{CI_CHECKS}}`, `{{LIBRARY_SECTIONS}}`) or, if the PRD gives no answer, delete the line and log an Open Question.
     - `code-standards.md` (from `templates/context/code-standards.md`): every "Rule That Cannot Be Broken" must end with `— enforced by: <check>`. If nothing enforces a rule, add the check to `verify.sh` or demote it to a convention.
     - `library-docs.md`: one section per library actually chosen, in the shape the template gives.
     - if the PRD has a UI: `ui-rules.md`, `ui-tokens.md`, `ui-registry.md`. Fill `{{PRODUCT_TYPE}}`, `{{BRANDING_NOTE}}` and `{{DOMAIN_STATUS_MAPPING}}` in `ui-tokens.md`; the token values are a neutral default and stay provisional until real branding exists.
6. **`AGENTS.md`** from `templates/AGENTS.md` and **`CLAUDE.md`** from `templates/CLAUDE.md`. Fill:
   - `{{READ_FIRST_LIST}}` — numbered list of the context files that exist (renumber; skip `ui-*` files if no UI; `progress-tracker.md` last)
   - `{{SOURCE_OF_TRUTH}}` — which document wins on what (PRD wins on function; stack decision doc/ADR wins on technology)
   - `{{CONSTRAINTS}}` — the PRD's hard constraints as short bullets, plus any the user confirmed in Step 4
   - `{{LANES}}` — the lane names
7. **Docs skeleton**: create `docs/adr/0001-stack-decision.md` (context, decision, consequences), and empty `docs/design/`, `docs/audit/`, `docs/operations/` each with a `.gitkeep`. **Only if the project has a relational database**: copy `templates/docs/erd/` (`generate_erd.py`, `README.md`), create `erd.config.json` from `erd.config.json.tmpl` and one `<context>.template.md` per bounded context from `diagram.template.md`.
8. **Other coding agents.** Ask which agents the team uses (Claude Code, Codex CLI, Gemini CLI, OpenCode, Cursor, Antigravity; multi-select). `AGENTS.md` is the shared instruction file that Codex, OpenCode, Cursor and Antigravity read. Then:
   - Gemini CLI / Antigravity: render `templates/adapters/GEMINI.md` to `GEMINI.md` (it imports `AGENTS.md`).
   - Cursor: copy `templates/adapters/harness.mdc` to `.cursor/rules/harness.mdc`.
   - Mirror the process skills into each chosen agent's project skills folder with `python3 "$HARNESS/scripts/install.py" --scope project --project-dir . --skills architect,imprint,review,recover,remember --agent <ids>` when `$HARNESS/scripts/install.py` exists, or by copying `$HARNESS/skills/*` to the folder listed in the agent's row of `agents/agents.json` (`.claude/skills`, `.codex/skills`, `.gemini/skills`, `.opencode/skills`, `.cursor/skills`, `.agent/skills`). Some of those paths are unconfirmed; say so in the report.
   - Hooks (`.claude/settings.json`) are Claude Code only. For every other agent the enforcement is `AGENTS.md` (tells the agent to run `bash scripts/verify.sh` before finishing) plus the git pre-push hook and CI. State this plainly in the report.
9. Ensure `.gitignore` exists; do not touch it if it does.

## Step 6 — Smoke-test

Run and report each result honestly:

- `bash -n` on every generated `.sh`
- `bash scripts/verify.sh --list` (must print the expected lanes) and `bash scripts/verify.sh --all --list`
- Every path referenced in `AGENTS.md` exists (`grep -o '`[a-z./_-]*`' AGENTS.md` and test each)
- No template placeholder remains in generated files: `grep -rnE '\{\{[A-Z_]+\}\}|@@[A-Z_]+@@|@(stack|when|optional|ecosystem):' AGENTS.md CLAUDE.md context scripts .github .claude` (GitHub expressions like `${{ github.ref }}` are lowercase and legitimate)
- If any check fails, fix it before reporting.

## Step 7 — Report

Short list: files created, files skipped (already existed), custom lanes written, placeholders/open questions still needing the user, and the exact next command:

```
bash scripts/install-hooks.sh     # once per clone: enable pre-push
/architect                        # plan task 00 / the first task in context/build-plan.md
```

Do not commit anything unless the user asks.
