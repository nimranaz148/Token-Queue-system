#!/usr/bin/env python3
"""
Read an existing spec (PRD / SOW / SRS) in any common format and turn it into Markdown.

    python3 read_spec.py <file> [--out spec.md] [--outline]

Supported: .md .markdown .txt  (as is) · .docx (headings, lists, tables, bold/italic) · .pdf (text extraction).
.doc / .odt / .rtf: not read directly; the tool tells you to export to .docx.

PDF text comes from the first available extractor: `pdftotext` (poppler) -> `pypdf` -> `PyMuPDF (fitz)`.
If none is installed the script exits with code 3 and says so: then read the PDF with your own file-reading
ability (most agents can read PDFs natively) or ask the user to export it to .docx / .md.

--outline prints only the heading tree (with line numbers) instead of the full text.
Standard library only (plus the optional PDF extractors above).
"""
import argparse
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


# ------------------------------------------------------------------ docx
def _text_of_run(r: ET.Element) -> str:
    out = []
    for c in r:
        if c.tag == W + "t":
            out.append(c.text or "")
        elif c.tag == W + "tab":
            out.append("\t")
        elif c.tag == W + "br":
            out.append(" ")
        elif c.tag in (W + "drawing", W + "pict"):
            out.append("[image]")
    return "".join(out)


def _run_md(r: ET.Element) -> str:
    t = _text_of_run(r)
    if not t.strip():
        return t
    rpr = r.find(W + "rPr")
    bold = italic = mono = False
    if rpr is not None:
        b = rpr.find(W + "b")
        bold = b is not None and b.get(W + "val", "1") not in ("0", "false")
        i = rpr.find(W + "i")
        italic = i is not None and i.get(W + "val", "1") not in ("0", "false")
        f = rpr.find(W + "rFonts")
        mono = f is not None and (f.get(W + "ascii") or "").lower() in ("consolas", "courier new", "courier")
    lead = t[: len(t) - len(t.lstrip())]
    trail = t[len(t.rstrip()):]
    core = t.strip()
    if mono:
        core = f"`{core}`"
    if bold and italic:
        core = f"***{core}***"
    elif bold:
        core = f"**{core}**"
    elif italic:
        core = f"_{core}_"
    return lead + core + trail


def _para_md(p: ET.Element) -> tuple[str, str, bool]:
    """returns (style, inline markdown, is_list)"""
    ppr = p.find(W + "pPr")
    style = ""
    is_list = False
    if ppr is not None:
        ps = ppr.find(W + "pStyle")
        if ps is not None:
            style = ps.get(W + "val", "")
        is_list = ppr.find(W + "numPr") is not None
    parts = []
    for child in p:
        if child.tag == W + "r":
            parts.append(_run_md(child))
        elif child.tag == W + "hyperlink":
            parts.extend(_run_md(r) for r in child.findall(W + "r"))
    text = "".join(parts)
    text = re.sub(r"\*\*(\s*)\*\*|__", "", text)
    text = re.sub(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", r"**\1\2**", text)  # merge adjacent bold runs
    return style, text.strip(), is_list


def _heading_level(style: str) -> int:
    m = re.match(r"(?i)^heading\s*(\d)$", style.replace(" ", ""))
    if m:
        return int(m.group(1))
    if style.lower() == "title":
        return 1
    return 0


def _table_md(tbl: ET.Element) -> list[str]:
    rows = []
    for tr in tbl.findall(W + "tr"):
        cells = []
        for tc in tr.findall(W + "tc"):
            paras = [_para_md(p)[1] for p in tc.findall(W + "p")]
            cell = "<br>".join(x for x in paras if x).replace("|", "\\|")
            cells.append(cell)
        rows.append(cells)
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def docx_to_md(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    out: list[str] = []
    for el in body:
        if el.tag == W + "p":
            style, text, is_list = _para_md(el)
            if not text:
                continue
            lvl = _heading_level(style)
            if lvl:
                out += ["", "#" * min(lvl + 1, 6) + " " + text if style.lower() != "title" else "# " + text, ""]
            elif is_list or "list" in style.lower():
                out.append("- " + text)
            else:
                out += [text, ""]
        elif el.tag == W + "tbl":
            out += [""] + _table_md(el) + [""]
    md = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


# ------------------------------------------------------------------ pdf
def pdf_text(path: Path) -> str | None:
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    try:
        from pypdf import PdfReader  # type: ignore
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    except Exception:
        pass
    try:
        import fitz  # type: ignore
        with fitz.open(str(path)) as d:
            return "\n".join(p.get_text() for p in d)
    except Exception:
        return None


def pdf_to_md(text: str) -> str:
    """Best effort: numbered short lines become headings; everything else stays as paragraphs."""
    out = []
    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            out.append("")
            continue
        m = re.match(r"^(\d{1,2})(\.(\d{1,2}))?\.?\s+([A-Z][^.!?]{2,78})$", s)
        if m and (m.group(3) or s.upper() == s or re.match(r"^\d{1,2}\.\s+[A-Z]", s)) and not s.endswith(","):
            out += ["", ("### " if m.group(3) else "## ") + s, ""]
        else:
            out.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


# ------------------------------------------------------------------ main
def outline(md: str) -> str:
    return "\n".join(f"{i:5d}  {l}" for i, l in enumerate(md.splitlines(), 1) if re.match(r"^#{1,4} ", l))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--out")
    ap.add_argument("--outline", action="store_true")
    a = ap.parse_args()
    p = Path(a.file)
    if not p.exists():
        print(f"not found: {p}", file=sys.stderr)
        return 2
    ext = p.suffix.lower()
    if ext in (".md", ".markdown", ".txt"):
        md = p.read_text(encoding="utf-8", errors="replace")
    elif ext == ".docx":
        md = docx_to_md(p)
    elif ext == ".pdf":
        t = pdf_text(p)
        if t is None:
            print("No PDF text extractor found (need `pdftotext`, `pypdf` or `PyMuPDF`).\n"
                  "Read the PDF with your own file-reading ability, or ask the user to export it to .docx or .md.", file=sys.stderr)
            return 3
        md = pdf_to_md(t)
    elif ext in (".doc", ".odt", ".rtf"):
        print(f"{ext} is not read directly. Ask the user to save it as .docx (or export to PDF / Markdown).", file=sys.stderr)
        return 4
    else:
        print(f"unsupported format: {ext}", file=sys.stderr)
        return 4
    result = outline(md) if a.outline else md
    if a.out:
        Path(a.out).write_text(result, encoding="utf-8", newline="\n")
        print(f"wrote {a.out} ({len(md.splitlines())} lines, {len(re.findall(r'^#{1,6} ', md, flags=re.M))} headings)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
