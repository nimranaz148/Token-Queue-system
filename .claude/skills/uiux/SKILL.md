---
name: uiux
description: Design and document the UI/UX of a website or app before it is built - a design system (tokens, typography, colour, motion language, budgets) and one standard page document per page - using the project's installed UI skills, at the motion level the PRD chose (cinematic 3D, refined, or minimal). Default is a whole-project overhaul; per-page brainstorming is the second mode. Use after the PRD and before or during bootstrap, or when the user wants a site to look award-winning, animated, 3D, GSAP/ScrollTrigger-driven, or redesigned.
---

# uiux — a design direction a senior designer would sign, written down before the code

You produce `docs/ui-ux/design-system.md` and one `docs/ui-ux/<page>/<page>.md` per page, then the build follows them. The goal is a first iteration that is already polished: distinctive, cohesive, accessible and fast, not a generic template that is "improved" over ten rounds.

Files next to this one:

- `references/page-standard.md` — the 11-part page document, with what each part must contain
- `references/design-system-standard.md` — required sections of `design-system.md`
- `references/motion-levels.md` — cinematic / refined / minimal, what each specifies, budgets and fallbacks
- `references/anti-slop.md` — the rules that stop the output looking templated
- `scripts/check_uiux.py` — validates the files you write (run it; fix every error)

## Non-negotiable rules

1. **Skills first.** Before designing, list the skills installed for this agent (the skills folders named in `agents/agents.json`, and `skills.lock`). Choose the ones that fit the project, say which and why, and use them. If the UI skill set is not installed, offer `honeys-spec-harness skills install --bundle ui` and wait for the answer; never invent that you used a skill that is not there.
2. **The PRD decides, you do not guess.** Read `docs/prd/PRD.md` (pages, forms, brand, audience, motion level in §16 or the interview log). Anything missing becomes a question to the user, not a default dressed as a fact.
3. **Distinctive, not default.** Palette and type are proposed from the brand and industry, justified in one line each, and confirmed by the user before pages are written. No generic SaaS look. Follow `references/anti-slop.md`.
4. **Motion has a job.** Every animation names its purpose: arrival, emphasis, transition or spatial continuity. Otherwise it does not ship.
5. **Budgets are part of done.** Performance and accessibility budgets are written into the design system and become checks (Lighthouse or equivalent lane, reduced-motion test). 3D and scroll effects fail there first.
6. **No invented content.** Copy comes from the PRD or is marked `[CLIENT TO CONFIRM]`.

## Step 0 — Mode and inputs

- **Overhaul (default):** the whole project gets a design system and every page document. Use when starting a site or reshaping an existing one.
- **Page mode:** brainstorm one page with the user, then write only that page's document, reusing the existing design system. Use when `design-system.md` already exists and the user names a page.

Read the PRD, `context/ui-*.md` if present, and the existing UI code if this is a redesign (screenshots or the running app when available).

## Step 1 — Skill review and direction

1. Inventory installed skills; select the relevant ones by role: design taste and anti-slop, typography, colour, layout, motion/animation, scroll and 3D, components and framework, accessibility, performance. List them in `design-system.md` under **Skills used**.
2. Ask the **motion level** if the PRD has not fixed it: `cinematic 3D` (recommended for marketing and brand sites), `refined motion`, or `minimal` (recommended for dense admin tools and dashboards, where heavy motion slows people down). The user decides.
3. Propose the direction in one short message: mood in three words, palette with roles, type pairing, the one signature motion idea. Wait for confirmation or changes.

## Step 2 — Inspiration research (once)

If `docs/ui-ux/inspiration.md` does not exist, research about fifteen award-calibre sites (start from the GSAP Showcase at gsap.com/showcase, Awwwards and similar), and for each record: URL, what it does well, the specific technique (for example pinned storytelling, clip-path wipes, WebGL hero), and whether it fits this brand. Write the file with the date. Reuse it afterwards; do not repeat the research unless the user asks. Never copy a site's content or branding; record techniques only.

## Step 3 — Design system

Write `docs/ui-ux/design-system.md` following `references/design-system-standard.md`: direction, tokens (colour, typography, spacing/grid, radius, elevation), the motion language for the chosen level (easing and duration tokens, patterns, reduced-motion and mobile rules), component rules, accessibility and performance budgets, and Skills used. Colours state contrast ratios for every text/background pair actually used.

## Step 4 — One document per page

For every page in the PRD navigation (§4) write `docs/ui-ux/<page>/<page>.md` following `references/page-standard.md`. Forms and screens in the PRD register (§5.2) that live on a page are referenced by their F-IDs. At the cinematic level each page also specifies: hero treatment, scroll storytelling (pinned sections, parallax, text and image reveals), page transitions, 3D usage and its fallback, and a mobile and reduced-motion variant that carries the same content.

## Step 5 — Validate and hand off

Run `python3 scripts/check_uiux.py docs/ui-ux` and fix every error it prints. Then report in at most 10 lines: motion level, palette and type, skills used, pages written, budgets, open questions. Tell the user the next step: build one page at a time from its document with `/architect` for the acceptance tests, then `bash scripts/verify.sh`.

## When building from the documents

Implement from the page document, not from memory. Use the selected skills for the craft (taste and layout skills while composing, motion skills for the animation pass, accessibility and performance skills before calling a page done). After the page works, run the motion review skills if installed (find opportunities, review, improve) and re-check the budgets.
