#!/usr/bin/env python3
"""
Structural validator for a PRD produced from references/prd-template.md.

    python3 check_prd.py docs/prd/PRD.md [--allow-placeholders]

Errors (exit 1): missing/invalid front matter, missing or out-of-order sections 0-38, leftover template
placeholders or comments, duplicate IDs, F-IDs used but never registered in section 5.2, phases without an exit
criterion. Warnings (exit 0): empty cells in the stack table, P0 form not mapped to a phase, section left as a
bare heading. Standard library only.
"""
import re
import sys
from pathlib import Path

PROFILES = {"prototype", "mvp", "production", "enterprise"}
FEATURES = {"tenancy", "audit", "money", "ui", "ai-agents", "api-contract", "database",
            "posted-documents", "offline", "compliance"}
REQUIRED_KEYS = ["project", "slug", "version", "status", "profile", "date", "owners", "stack", "features", "layout", "phases"]
ID_KINDS = {"F": "form", "D": "dashboard", "R": "report", "W": "workflow", "I": "integration", "A": "assumption", "Q": "question"}


def parse_front_matter(text: str):
    m = re.match(r"^<!--.*?-->\s*\n?", text, flags=re.S)
    body = text[m.end():] if m else text
    fm = re.match(r"^---\n(.*?)\n---\n", body, flags=re.S)
    if not fm:
        return None, body
    data: dict = {}
    key = None
    for raw in fm.group(1).splitlines():
        line = raw.split("#", 1)[0].rstrip() if not raw.lstrip().startswith("-") else raw.rstrip()
        if not line.strip():
            continue
        if re.match(r"^\S", line):
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            data[key] = v if v else ([] if key == "features" else {})
        elif line.lstrip().startswith("-") and isinstance(data.get(key), list):
            data[key].append(line.lstrip()[1:].strip().strip('"'))
        elif isinstance(data.get(key), dict):
            k, _, v = line.strip().partition(":")
            data[key][k.strip()] = v.strip().strip('"')
        elif line.lstrip().startswith("-") and key:
            data[key] = [line.lstrip()[1:].strip().strip('"')]
    if isinstance(data.get("features"), str):
        inner = data["features"].strip("[] ")
        data["features"] = [x.strip().strip('"') for x in inner.split(",") if x.strip()]
    return data, body[fm.end():]


def sections(body: str) -> dict[str, tuple[int, str]]:
    """Map section number -> (line index, text until next ## heading)."""
    lines = body.splitlines()
    idx = [(i, re.match(r"^## (\d+)\. ", l)) for i, l in enumerate(lines)]
    idx = [(i, int(m.group(1))) for i, m in idx if m]
    out = {}
    for n, (i, num) in enumerate(idx):
        end = idx[n + 1][0] if n + 1 < len(idx) else len(lines)
        out[str(num)] = (i, "\n".join(lines[i:end]))
    return out


def table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if line.strip().startswith("|") and not re.match(r"^\s*\|[\s:|-]+\|\s*$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    allow_ph = "--allow-placeholders" in sys.argv
    if len(args) != 1:
        print(__doc__)
        return 2
    text = Path(args[0]).read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    fm, body = parse_front_matter(text)
    if fm is None:
        errors.append("front matter (--- … ---) missing at the top of the file")
        fm = {}
    else:
        for k in REQUIRED_KEYS:
            if k not in fm or fm[k] in ("", [], {}):
                errors.append(f"front matter: '{k}' missing or empty")
        if fm.get("profile") not in PROFILES:
            errors.append(f"front matter: profile must be one of {sorted(PROFILES)}")
        if not re.match(r"^\d+\.\d+\.\d+$", str(fm.get("version", "")).strip('"')):
            errors.append("front matter: version must be semver (e.g. 0.1.0)")
        bad = [f for f in fm.get("features", []) if f not in FEATURES]
        if bad:
            errors.append(f"front matter: unknown features {bad}; allowed: {sorted(FEATURES)}")
        if not str(fm.get("phases", "")).strip().isdigit():
            errors.append("front matter: phases must be an integer")

    secs = sections(body)
    last = -1
    for n in range(0, 39):
        s = secs.get(str(n))
        if s is None:
            errors.append(f"section {n} heading missing (expected '## {n}. …')")
            continue
        if s[0] < last:
            errors.append(f"section {n} is out of order")
        last = s[0]
        content = [l for l in s[1].splitlines()[1:] if l.strip() and not l.startswith("#")]
        if not content:
            warnings.append(f"section {n} has no content under its heading")

    if not allow_ph:
        ph = sorted(set(re.findall(r"\{\{[^}]*\}\}", text)))
        if ph:
            errors.append(f"template placeholders left: {', '.join(ph[:8])}{' …' if len(ph) > 8 else ''}")
        if re.search(r"<!--\s*(PRD TEMPLATE|Rules for filling)", text):
            errors.append("template instruction comment still present")

    # IDs
    reg: dict[str, list[str]] = {}
    for line in body.splitlines():
        m = re.match(r"^\|\s*\**(F|D|R|W|I|A|Q)-(\d+)\**\s*\|", line)
        if m:
            reg.setdefault(f"{m.group(1)}-{m.group(2)}", []).append(line[:60])
    for k, v in ID_KINDS.items():
        pass
    for id_, lines in reg.items():
        if id_.startswith(("F", "D", "R", "I", "A", "Q")) and len(lines) > 1 and not id_.startswith("F"):
            errors.append(f"duplicate {ID_KINDS[id_[0]]} ID {id_} registered {len(lines)} times")

    s5 = secs.get("5", (0, ""))[1]
    reg52 = set(re.findall(r"^\|\s*(F-\d+)\s*\|", s5.split("### 5.3")[0], flags=re.M))
    dup52 = [f for f in reg52 if len(re.findall(rf"^\|\s*{f}\s*\|", s5.split('### 5.3')[0], flags=re.M)) > 1]
    for f in dup52:
        errors.append(f"form ID {f} registered twice in section 5.2")
    used = set(re.findall(r"\bF-\d{3}\b", body))
    missing = sorted(used - reg52)
    if missing:
        errors.append(f"form IDs used but not in the section 5.2 register: {', '.join(missing[:10])}")

    # phases
    s22 = secs.get("22", (0, ""))[1]
    rows = table_rows(s22)
    phase_rows = [r for r in rows[1:] if r and re.match(r"^\d+$", r[0])]
    if len(phase_rows) < 1:
        errors.append("section 22 has no phase rows")
    for r in phase_rows:
        if len(r) < 3 or not r[2] or r[2].startswith("_"):
            errors.append(f"phase {r[0]} has no exit criterion")
    if fm.get("phases", "").isdigit() and phase_rows and int(fm["phases"]) != len(phase_rows) and int(fm["phases"]) != len(phase_rows) - 1:
        warnings.append(f"front matter phases={fm['phases']} but section 22 lists {len(phase_rows)} phase rows (phase 0 may be extra)")
    phases_listed = {r[0] for r in phase_rows}

    # P0 forms mapped to a phase
    for r in table_rows(s5.split("### 5.3")[0]):
        if r and re.match(r"^F-\d+$", r[0]) and len(r) >= 7 and r[5].startswith("P0"):
            if r[6] not in phases_listed and phase_rows:
                warnings.append(f"{r[0]} is P0 but its phase '{r[6]}' is not in section 22")

    # stack table
    s3 = secs.get("3", (0, ""))[1]
    empties = [r[0] for r in table_rows(s3.split("### 3.2")[0])[1:] if len(r) >= 3 and (not r[1] or not r[2]) and r[0] not in ("Layer",)]
    if empties:
        warnings.append(f"stack table has empty cells for: {', '.join(empties[:8])} (fill or write n/a)")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error:   {e}")
    print(f"{'FAILED' if errors else 'OK'}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
