#!/usr/bin/env python3
"""
Map an existing spec (already converted to Markdown by read_spec.py) onto the 38-section PRD template.

    python3 gap_map.py existing-spec.md [--json]

For each template section 0-38 it reports: present (heading found with real content), thin (found but almost empty),
renamed (found under a different title, matched by number/keywords), or missing. It also lists headings in the
existing spec that match no template section ("unmapped"): those must be kept (moved to an appendix), never dropped.
Standard library only.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

TEMPLATE = {
    0: "Document Control", 1: "Executive Summary", 2: "Product Objectives", 3: "Technology & Architecture",
    4: "Application Navigation / Main Menu", 5: "Form & Screen Specification", 6: "Key Screen Detailed Requirements",
    7: "Dashboards", 8: "Dashboard UI Standard", 9: "Reports", 10: "Core Business Workflows",
    11: "Offline & Synchronization", 12: "Database / Data Model", 13: "API Requirements", 14: "Security & Audit",
    15: "AI-Assisted Development Protocol", 16: "UI/UX Standards", 17: "Performance Requirements",
    18: "Backup & Disaster Recovery", 19: "Testing & Acceptance", 20: "Acceptance Criteria for Forms",
    21: "Acceptance Criteria for Dashboards", 22: "Phased Delivery Plan", 23: "Required Deliverables",
    24: "Definition of Done", 25: "Change Control", 26: "Initial Feature Priority", 27: "Final Product Structure",
    28: "Approval", 29: "Visual UI / UX Wireframes Dashboards", 30: "Visual Form Wireframes",
    31: "Visual Design Rules for Implementation", 32: "UI Acceptance Checklist", 33: "Note on Final UI Design",
    34: "Mandatory Compliance / Regulatory Integration Requirement", 35: "Mandatory P0 Compliance Requirement",
    36: "Mandatory Agentic AI Architecture", 37: "Updated Master Priority", 38: "Final Architectural Principle",
}
# words that identify a section even when the title was changed (e.g. a product-specific screen name for "Key Screen")
HINTS = {
    0: ["document control", "revision", "version history"], 1: ["executive summary", "overview", "introduction"],
    2: ["objective", "goals"], 3: ["technology", "architecture", "tech stack"], 4: ["navigation", "menu"],
    5: ["form", "screen specification"], 6: ["screen", "detailed requirements"], 7: ["dashboard"], 8: ["dashboard ui"],
    9: ["report"], 10: ["workflow", "business process"], 11: ["offline", "synchron"], 12: ["database", "data model"],
    13: ["api"], 14: ["security", "audit"], 15: ["development protocol", "ai development"], 16: ["ui/ux", "ux standard"],
    17: ["performance"], 18: ["backup", "disaster"], 19: ["testing"], 20: ["acceptance criteria for forms"],
    21: ["acceptance criteria for dashboards"], 22: ["phase", "delivery plan", "roadmap"], 23: ["deliverable"],
    24: ["definition of done"], 25: ["change control", "change request"], 26: ["priority", "moscow"],
    27: ["product structure"], 28: ["approval", "sign-off", "sign off"], 29: ["wireframe"], 30: ["form wireframe"],
    31: ["design rules"], 32: ["ui acceptance", "acceptance checklist"], 33: ["final ui design"],
    34: ["compliance", "regulatory", "tax authority", "integration requirement"], 35: ["p0 compliance"],
    36: ["agentic", "ai architecture"], 37: ["master priority"], 38: ["architectural principle"],
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()


def sections(md: str) -> list[dict]:
    lines = md.splitlines()
    heads = [(i, len(m.group(1)), m.group(2).strip()) for i, l in enumerate(lines) if (m := re.match(r"^(#{1,4})\s+(.*)$", l))]
    out = []
    for n, (i, lvl, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        body = [l for l in lines[i + 1:end] if l.strip() and not l.startswith("#")]
        num = re.match(r"^(\d{1,2})(?:\.\d+)*\.?\s", title)
        out.append({"line": i + 1, "level": lvl, "title": title, "num": int(num.group(1)) if num else None,
                    "sub": bool(re.match(r"^\d+\.\d+", title)), "body": len(body),
                    "tables": sum(1 for l in body if l.startswith("|") and "---" in l)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    secs = sections(Path(a.file).read_text(encoding="utf-8"))
    tops = [s for s in secs if not s["sub"]]
    used: set[int] = set()
    cands = []
    for n, title in TEMPLATE.items():
        for idx, s in enumerate(tops):
            t = re.sub(r"^\d+(\.\d+)*\.?\s*", "", s["title"])
            ratio = difflib.SequenceMatcher(None, norm(title), norm(t)).ratio()
            hint = any(h in norm(t) for h in HINTS.get(n, []))
            if n == 0 and not hint:  # section 0 (document control) only matches on explicit wording
                continue
            sc = ratio + (0.25 if hint else 0) + (0.2 if s["num"] == n else 0)
            if sc >= 0.55:
                cands.append((sc, n, idx, ratio))
    chosen: dict[int, tuple[int, float]] = {}
    for sc, n, idx, ratio in sorted(cands, reverse=True):  # best matches first, each side used once
        if n not in chosen and idx not in used:
            chosen[n] = (idx, ratio)
            used.add(idx)
    result = []
    for n, title in TEMPLATE.items():
        if n not in chosen:
            result.append({"section": n, "template": title, "status": "missing", "found": None, "line": None})
            continue
        idx0, ratio = chosen[n]
        s = tops[idx0]
        idx = secs.index(s)
        body, tables = s["body"], s["tables"]
        for sub in secs[idx + 1:]:
            if sub["sub"]:
                body += sub["body"]
                tables += sub["tables"]
            else:
                break
        status = "thin" if body < 3 and tables == 0 else ("present" if ratio > 0.85 else "renamed")
        result.append({"section": n, "template": title, "status": status, "found": s["title"], "line": s["line"], "content_lines": body, "tables": tables})
    unmapped = [{"line": s["line"], "title": s["title"]} for i, s in enumerate(tops) if i not in used and s["level"] <= 2]
    if a.json:
        print(json.dumps({"sections": result, "unmapped": unmapped}, indent=2))
        return 0
    counts = {k: sum(1 for r in result if r["status"] == k) for k in ("present", "renamed", "thin", "missing")}
    print("| # | Template section | Status | Found as |\n| --- | --- | --- | --- |")
    for r in result:
        print(f"| {r['section']} | {r['template']} | {r['status']} | {r['found'] or ''} |")
    print(f"\nSummary: {counts['present']} present, {counts['renamed']} renamed, {counts['thin']} thin, {counts['missing']} missing")
    if unmapped:
        print("\nUnmapped headings (keep them: move to an appendix, never drop):")
        for u in unmapped:
            print(f"- line {u['line']}: {u['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
