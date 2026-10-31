#!/usr/bin/env python3
"""Validate docs/ui-ux (design-system.md plus one document per page).

    python3 check_uiux.py docs/ui-ux

Errors (exit 1): missing or out-of-order sections, a motion level that is not cinematic/refined/minimal,
no contrast ratios, no numeric budgets, a page without reduced-motion/mobile handling, lorem ipsum or
template placeholders, no page documents. Warnings (exit 0): no inspiration.md for a cinematic design.
Standard library only.
"""
import re
import sys
from pathlib import Path

DS_SECTIONS = ["direction", "motion level", "colour tokens", "typography", "spacing and grid", "motion language", "components", "accessibility and performance budgets", "skills used"]
PAGE_SECTIONS = ["page overview", "section-by-section breakdown", "content", "layout structure", "component breakdown", "visual hierarchy", "ctas", "media", "interactions", "diagram", "notes"]
LEVELS = ("cinematic", "refined", "minimal")
BAD = re.compile(r"lorem ipsum|\{\{[A-Z_]+\}\}|<!--\s*(todo|fill)", re.I)


def headings(text: str):
    return [(int(m.group(1)), m.group(2).strip().lower()) for m in re.finditer(r"^## (\d+)\.\s+(.+)$", text, re.M)]


def section(text: str, num: int) -> str:
    m = re.search(rf"^## {num}\.\s+.*$", text, re.M)
    if not m:
        return ""
    n = re.search(r"^## \d+\.\s+", text[m.end():], re.M)
    return text[m.end(): m.end() + n.start()] if n else text[m.end():]


def check_order(path: Path, text: str, expected: list[str], errs: list[str]) -> None:
    got = headings(text)
    for i, name in enumerate(expected, 1):
        hit = [t for n, t in got if n == i]
        if not hit:
            errs.append(f"{path}: missing section '## {i}. {name.title()}' (add it with that heading)")
        elif not hit[0].startswith(name.split(" ")[0]) and name not in hit[0]:
            errs.append(f"{path}: section {i} is '{hit[0]}' but should be '{name}'")
    nums = [n for n, _ in got]
    if nums != sorted(nums):
        errs.append(f"{path}: sections are out of order")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/ui-ux")
    errs: list[str] = []
    warns: list[str] = []
    ds = root / "design-system.md"
    level = ""
    if not ds.is_file():
        errs.append(f"{ds}: missing (write the design system first)")
    else:
        t = ds.read_text(encoding="utf-8")
        check_order(ds, t, DS_SECTIONS, errs)
        found = [l for l in LEVELS if re.search(rf"\b{l}\b", section(t, 2).lower())]
        if len(found) != 1:
            errs.append(f"{ds}: section 2 must name exactly one motion level: cinematic, refined or minimal")
        else:
            level = found[0]
        if not re.search(r"\d(\.\d+)?\s*:\s*1", section(t, 3)):
            errs.append(f"{ds}: section 3 has no contrast ratios (write e.g. '15.8:1' for each text/background pair used)")
        b = section(t, 8).lower()
        if not (re.search(r"\d+\s*(kb|kib|ms|gzip)", b) and "reduced-motion" in b.replace("prefers-reduced-motion", "reduced-motion")):
            errs.append(f"{ds}: section 8 needs numeric budgets (KB / ms / gzip) and the reduced-motion rule")
        if "reduced" not in section(t, 6).lower():
            errs.append(f"{ds}: section 6 (motion language) must give a reduced-motion rule")
        if BAD.search(t):
            errs.append(f"{ds}: contains lorem ipsum or an unfilled placeholder")
    pages = sorted(p for p in root.glob("*/*.md") if p.parent.name == p.stem)
    if not pages:
        errs.append(f"{root}: no page documents (expected docs/ui-ux/<page>/<page>.md)")
    for p in pages:
        t = p.read_text(encoding="utf-8")
        check_order(p, t, PAGE_SECTIONS, errs)
        if BAD.search(t):
            errs.append(f"{p}: contains lorem ipsum or an unfilled placeholder")
        inter = section(t, 9).lower()
        if "reduced" not in inter or "mobile" not in inter:
            errs.append(f"{p}: section 9 (Interactions) must give the mobile and reduced-motion variants")
        if level == "cinematic" and not ("scroll" in inter and "fallback" in (inter + section(t, 8).lower())):
            errs.append(f"{p}: cinematic level: section 9 must describe scroll storytelling and section 8/9 the fallback for 3D or heavy media")
    if level == "cinematic" and not (root / "inspiration.md").is_file():
        warns.append(f"{root / 'inspiration.md'} is missing: run the inspiration research once and save it there")
    for e in errs:
        print(f"✗ uiux: {e}")
    for w in warns:
        print(f"⚠ uiux: {w}")
    if errs:
        print("  next: fix the lines above, then run this check again")
        return 1
    print(f"uiux: ok ({len(pages)} page document(s), level {level or 'unknown'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
