# Update Protocol (existing PRD / SOW)

Used when Step 0 of the `prd` skill finds a spec. The goal is to change what needs changing, keep everything else, and leave a trail.

## 1. Read and map

1. **Read it, whatever the format.** `python3 scripts/read_spec.py <file> --out docs/prd/existing-spec.md`
   - `.md` / `.txt`: read as is · `.docx`: headings, lists, tables and bold/italic are preserved · `.pdf`: text is extracted (`pdftotext`, `pypdf` or `PyMuPDF`) and numbered headings are recovered heuristically
   - exit code 3 = no PDF extractor installed: read the PDF natively or ask the user for `.docx`/`.md`; exit code 4 = `.doc`/`.odt`/`.rtf`: ask the user to save as `.docx`
   - Keep IDs (F-001…, or the document's own scheme) exactly as written.
   - Check the conversion: run `python3 scripts/read_spec.py <file> --outline` and compare the heading list with what the user expects. PDF conversions are the least reliable: say so and confirm the outline with the user.
2. Read `docs/prd/discovery-log.md` if present, and the repo (`context/progress-tracker.md`, `git log`) to see what has already been built.
3. **Gap map:** `python3 scripts/gap_map.py docs/prd/existing-spec.md`. It marks each template section 0-38 as `present`, `renamed`, `thin` or `missing`, and lists **unmapped** headings (content the template has no section for).
4. Show the gap map to the user in a compact table and ask what they want: *a specific change*, *fill the gaps*, or *both*. Also ask: **"Is anything in this document you do not want carried over?"** The user decides what stays; nothing is dropped without their yes.

## 2. Convert if needed

If the source is not already in the 38-section shape:
- Offer to **restructure into the template** (keeping every existing ID, field and requirement, moving text under the matching section).
- Never drop content. Anything that has no home goes in an "Unmapped material" appendix and is reported.
- Write the converted document to `docs/prd/PRD.md` and keep the original file untouched. Then generate `docs/prd/PRD.docx` with `scripts/md_to_docx.py` so the user has the restructured Word version too.

## 3. Interview only for what changes

- For a specific change: ask the rounds in `interview.md` that the change touches (e.g. new module → Round 3 for that module, Round 5 services it needs, Round 7 integrations).
- For gaps: ask only the questions needed to fill `thin`/`missing` sections.
- Skip anything the document or discovery log already answers. Quote the existing answer and ask "still true?" only for decisions older than the current profile or stack.

## 4. Impact analysis before editing

Before touching the file, list for the user:
- sections that will change
- IDs that will be added / changed / retired (never reuse a retired ID; mark it `retired in vX.Y.Z`)
- effects on phases and P0 scope
- effects already-built work (compare with `progress-tracker.md`): mark items **rework required**
- effects on the stack table and on `context/`/`AGENTS.md` if the harness was already bootstrapped (tell the user to re-run `bootstrap` in update mode)

Get a yes.

## 5. Edit rules

- Edit in place. Keep unrelated sections byte-for-byte.
- **Version bump** (semver in front matter `version`):
  - MAJOR — stack change, scope removed, profile change, architecture constraint changed
  - MINOR — new module, form, workflow, integration or phase
  - PATCH — clarification, wording, filled gap, corrected number
- Add a row to §0.2 Revision history: version, date, author, summary, sections touched.
- For any scope change relative to an **approved** PRD (`status: approved`), also add a row to §25.1 Change request log and set `status: in-review` until re-approved.
- Stack or architecture changes also get an ADR in `docs/adr/NNNN-<title>.md` (context, decision, consequences) — create it or tell the user to.
- New assumptions → §0.3; new unknowns → §0.4; decisions → Appendix A.

## 6. Validate and report

- Run the validator (or the manual checklist in SKILL.md Step 6), then regenerate `PRD.docx`.
- Report: version before → after, sections changed, IDs added/retired, assumptions and open questions added, rework flagged, and whether `bootstrap` needs to be re-run.
