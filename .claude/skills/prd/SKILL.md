---
name: prd
description: Create or update a full PRD / SOW / technical specification (38 numbered sections - objectives, stack decision record, forms, data model, APIs, security, phases, acceptance, AI architecture) through a dense discovery interview about ambition (prototype vs production), budget (free/open-source vs paid), scale, pages, phases, stack (Next.js, FastAPI, .NET, MERN, Go, Spring...), services (Redis, queues, search, auth, storage) and integrations. Use when the user wants a PRD, SOW, SRS, product spec or requirements document, has no spec yet, or wants to revise an existing one. Output feeds the bootstrap skill.
---

# prd — discovery interview to a hand-off-ready PRD

You turn a vague idea into a dense, testable Product Requirements & Technical Specification, or you update one that already exists.
The document has a fixed 38-section structure so every project gets the same shape and other skills (`bootstrap`, `architect`, `review`) can cite sections.

This skill is self-contained and works in any agent that loads `SKILL.md` skills (Claude Code, claude.ai, Codex CLI, Gemini CLI, OpenCode, Cursor, Antigravity).
Files you need sit next to this file:

- `references/interview.md` — the question bank, round by round, with skip rules
- `references/stacks.md` — profiles, stack presets, recommendation rules, page/phase heuristics
- `references/prd-template.md` — the document skeleton (sections 0-38 plus appendices)
- `references/update-protocol.md` — how to revise an existing PRD safely
- `scripts/read_spec.py` — reads an existing spec in **.md, .txt, .docx or .pdf** and converts it to Markdown
- `scripts/gap_map.py` — maps an existing spec onto the 38 sections (present / renamed / thin / missing / unmapped)
- `scripts/md_to_docx.py` — turns the finished PRD into a Word `.docx` (standard library only)
- `../../packs/<id>/` (or `harness/packs/` when bundled) — per-project-type packs: `interview.md` (technical questions with a recommendation and a free-tier default), `checklist.md`, `phases.md`; select them with `python3 scripts/packs.py detect docs/prd/PRD.md`
- `scripts/reverse_prd.py` — reads a **built codebase** and writes findings (stack, layout, pages, endpoints, entities, tests) with a confidence and source file per row
- `scripts/check_prd.py` — structural validator (run it if you have a shell; otherwise apply its checks by hand, listed in Step 6)

Tool note: when your environment has a structured question tool (Claude Code `AskUserQuestion`, or similar) use it for choice questions,
with the recommended option first. Otherwise ask numbered plain-text questions. Never ask more than five questions at once.

## Non-negotiable rules

1. **Interview before writing.** Do not draft the PRD from a one-line idea. The interview is the product of this skill.
2. **Ask intelligently.** Skip anything already answered; skip conditional questions whose trigger is false (no Salesforce question unless the product has a customer/sales pipeline; no Redis question until load, queues, rate limits or realtime come up).
3. **Recommend, do not survey.** Every choice question puts a recommendation first with a one-line reason.
4. **Never invent facts.** Numbers the user did not give are offered as ranges and recorded as assumptions. Unknowns become Open Questions.
5. **Delegation is allowed and recorded.** "You decide" means pick the recommendation and write it in §0.3 Assumptions.
6. **Do not overwrite.** Existing PRD content is edited in place with a revision entry, never silently replaced.
7. **Keep the numbering.** Sections that do not apply stay, marked `Not applicable — <reason>`.
8. **No secrets** in any file this skill writes.

## Step 0 — Detect mode

Look for an existing spec: `docs/prd/PRD.md`, `PRD.md`, `SOW.md`, `SRS.md`, any `.md`, `.docx` or `.pdf` with PRD/SOW/SRS/spec/requirements in its name, or a path the user gave. Ask the user if they have one elsewhere (email attachment, Drive, Notion export).

- Found (in **any** format) → **Update mode**. Read it with `python3 scripts/read_spec.py <file> --out docs/prd/existing-spec.md`
  (handles `.md`, `.docx`, `.pdf`; if it exits with code 3 there is no PDF extractor: read the PDF with your own file ability or ask for a `.docx`/`.md`),
  then read `references/update-protocol.md` and continue with that protocol.
- Not found, but the repo already contains a built application (manifests, routes, pages, a schema) → **Reverse mode**. Run
  `python3 scripts/reverse_prd.py . --out docs/prd/reverse-findings.md --name "<project name>"`, read the findings, then interview **only** for what the code cannot say
  (purpose, users and roles, scope going forward, acceptance rules, phases, non-functional targets). Write the PRD from the findings plus the answers; mark every statement that came
  from code only as *observed* and every answer as *confirmed by owner*; keep the findings file next to the PRD. Never present a guess about intent as fact.
- Not found and no built application → **Create mode**.

Also look at the repo (manifests, folders, `context/`, `AGENTS.md`) for facts you should not ask about again.

## Step 1 — Open with the seed and the profile

Run Round 0 and Round 1 from `references/interview.md` (idea, existing assets, ambition, budget, team, hosting, licensing).
The answers set the **profile** (`prototype | mvp | production | enterprise`), which changes every later default in `references/stacks.md`.
Say the profile out loud and get a confirmation before continuing.

## Step 2 — Scale, shape and features

Run Rounds 2 and 3: users and roles, tenancy, data volume, **how many frontend pages** (offer the ranges), devices, modules and P0-P3 priorities, reports/dashboards, documents that get posted, audit, offline, compliance, and **how many phases** (propose a number from `stacks.md`, let the user change it, and get an exit test for each phase).

## Step 3 — Stack, services and AI

**Packs.** After the profile and features are known, run `python3 <harness>/scripts/packs.py detect <PRD or draft front matter>` (or pick from `packs/`: web-app, marketing-3d-site, backend-api, integrations, agents, devops-infra, voice-agents). For each selected pack, ask its `interview.md` questions in place of generic ones, put its `checklist.md` items into the PRD as requirements to answer before Phase 1 exits, and list its packs in the front matter as `packs: [web-app, backend-api]` so `bootstrap` can add the pack tasks and deferred triggers. A project may use several packs. The core interview works with none.

**Technical interview rule (create mode):** recommend first, then ask only what changes the build. For each decision give one recommendation, the one-line reason, the free-tier default, and the trigger for moving up; the user answers "yes" or names a change. Do not ask a question whose answer would not alter a task, a lane or a cost. Phase 0 and Phase 1 are a production MVP: record anything bigger as *deferred, with its trigger* in §3.2.

Run Rounds 4-7. Order matters:

1. If the user has a preferred stack, restate it and check it against the profile and scale. Flag only genuine mismatches.
2. Otherwise give **one** recommendation with its reasoning (4-6 lines), the exit ramp for 10x growth, and at most one alternative.
3. Walk the services table in Round 5 **only for the rows whose trigger is true**. For Redis, queues, search, Kubernetes and microservices, the default answer is "not now"; record them in PRD §3.2 *Considered and deferred* with a measurable trigger.
4. Ask the AI questions only if the product will have AI features (Round 6). If yes, the AI service is a client of the API and never holds database credentials.
5. Ask about integrations only where the domain implies them (Round 7).

## Step 3b — Skills for the chosen stack

Once the stack is confirmed, map it to skills the project should have: read `references/stacks.md` (section *Stack to skill tags*) and, if the harness `skills-manifest.json` is available, resolve each tag to a manifest entry. Show the list (name, source repository, licence) and install only on confirmation. Never copy third-party skill text into the PRD or the repo; the manifest pins each skill to a commit. If a tag has no upstream skill (for example a vendor integration), say so and offer to generate a project-local skill from current vendor documentation, citing the URL and date. For any website, offer the UI skill set and ask the motion level (cinematic 3D, refined motion, minimal); recommend cinematic for marketing and brand sites and a calmer level for dense tools.

## Step 4 — Non-functional and delivery, then confirm

Run Round 8. Then present the **Decision Summary** and wait for confirmation or corrections:

```
Decision Summary
Profile: <profile>            Budget: <free/OSS | low | comfortable | open>
Users: <n roles, ~n users>    Tenancy: <single | multi-branch | multi-tenant>
Pages: ~<n>                   Phases: <n> (Phase 0 = foundation)
Stack: <frontend> + <backend> + <database/migrations> + <agents>
Services adopted: <list>      Considered and deferred: <list + trigger>
P0: <list>                    Compliance: <list or none>
Assumptions I made: <list>    Open questions: <list>
```

Save the raw answers as you go to `docs/prd/discovery-log.md` (round, question, answer, date). Update mode reads this file to avoid re-asking.

## Step 5 — Write the PRD

Target file: `docs/prd/PRD.md` (or the existing PRD path in update mode).
Start from `references/prd-template.md`; fill the front matter first — `bootstrap` reads it to skip its own questions.

Front matter must contain: `project, slug, version, status, profile, date, owners, stack{…}, features[…], layout{…}, phases`.
`features` may only use: `tenancy, audit, money, ui, ai-agents, api-contract, database, posted-documents, offline, compliance`.

Write **section by section** (not one giant output), in this order, telling the user which section you are on:

1. §0-§2 (control, summary, objectives, metrics, out of scope)
2. §3 (stack decision record — every cell filled or "n/a", deferred list, architecture diagram, layout, tenancy, constraints)
3. §5, §12, §13 together (form register with IDs, field specs, data model, API register) so IDs and names stay consistent
4. §4, §6-§11 (navigation, key screens, dashboards, reports, workflows, offline)
5. §14-§21 (security, dev protocol, UI standards, performance, DR, testing, acceptance)
6. §22-§28 (phases with exit tests, deliverables, DoD, change control, priorities, structure, approval)
7. §29-§33 (wireframes as ASCII, design rules, checklist) — for every P0 form at least
8. §34-§38 (compliance, agentic AI, master priority, final principle) — `Not applicable` where they do not apply
9. Appendices A-C (decisions, risks, cost profile)

Depth rules — this is where "dense" comes from:
- Every module has forms (with IDs), fields (type, required, rule), workflows (numbered steps and states), reports, permissions and audited actions.
- Every P0 form has a field table and an ASCII wireframe whose field names match §5.3 exactly.
- Every phase has scope, dependencies and an exit test a person can run.
- Every requirement uses "shall" and is testable; performance and scale statements carry numbers.
- Technical detail is included: table names, endpoint paths, state machines, idempotency, indexes, error format, environments.

## Step 5b — Produce the Word version

Immediately after writing the Markdown PRD, generate the Word document unless the user said they only want Markdown:

```
python3 scripts/md_to_docx.py docs/prd/PRD.md docs/prd/PRD.docx
```

Both files are deliverables. **`PRD.md` is the source of truth** (diffable, validated, read by `bootstrap`); `PRD.docx` is for people who work in Word.
If someone edits the `.docx`, bring the edits back with `read_spec.py PRD.docx --out PRD.md` (update mode does this for you) and regenerate the `.docx` afterwards.
If you cannot run scripts, say so and tell the user the exact commands to run.

## Step 6 — Validate

If you have a shell: `python3 <this-skill>/scripts/check_prd.py docs/prd/PRD.md` and fix every error it prints (warnings: fix or justify).
Without a shell, check by hand:

- front matter present and complete; `features` values are from the allowed list
- headings §0-§38 all present and in order
- no `{{…}}` placeholder and no template HTML comment left
- every ID (F-, D-, R-, W-, I-, A-, Q-) is unique; every F-ID in §5.3/§30 also exists in §5.2
- every phase in §22 has an exit criterion; every P0 item is scheduled in a phase
- §3.1 has no empty cell; anything not adopted appears in §3.2
- assumptions are in §0.3, unknowns in §0.4

## Step 7 — Hand off

Report in ≤10 lines: files written (`PRD.md` and `PRD.docx`), profile, stack, phases, page count, number of forms/dashboards/reports, open questions still blocking, assumptions to confirm.
Then tell the user the next command: run the `bootstrap` skill (`/bootstrap docs/prd/PRD.md` in Claude Code, or ask the agent to "run the bootstrap skill on docs/prd/PRD.md").
Do not commit unless asked.
