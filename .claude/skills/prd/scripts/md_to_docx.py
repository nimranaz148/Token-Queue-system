#!/usr/bin/env python3
"""
Convert the PRD (Markdown with optional YAML front matter) into a Word .docx. Standard library only.

    python3 md_to_docx.py docs/prd/PRD.md docs/prd/PRD.docx [--no-cover] [--title "Override title"]

What it renders: cover page + document-control table (from the front matter), contents list, headings
(## -> Heading 1, ### -> Heading 2, #### -> Heading 3), paragraphs with **bold**, *italic* / _italic_ and `code`,
bullet and numbered lists (nested), checkbox items, tables (header row shaded and repeated across pages),
fenced code blocks (monospace, shaded), block quotes, page-number footer. HTML comments are dropped.

The Markdown file stays the source of truth (diffable, validated by check_prd.py); the .docx is the deliverable for
people who work in Word. To bring Word edits back: `python3 read_spec.py PRD.docx --out PRD.md`.
"""
import argparse
import datetime
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HONEY, DARK, GREY = "F5A623", "3B2A14", "F2F2F2"
TEXT_W = 9638  # A4 with 2 cm margins, in twips


# ---------------------------------------------------------------- inline
def parse_inline(text: str) -> list[tuple[str, frozenset]]:
    """-> [(text, {'b','i','c'})]"""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    segs: list[tuple[str, frozenset]] = []

    def emit(t: str, fmt: frozenset) -> None:
        # bold, then italics inside plain segments
        parts = re.split(r"(\*\*[^*]+\*\*|__[^_]+__)", t)
        for part in parts:
            if not part:
                continue
            if (part.startswith("**") and part.endswith("**") and len(part) > 4) or (part.startswith("__") and part.endswith("__") and len(part) > 4):
                inner = part[2:-2]
                emit_italic(inner, fmt | {"b"})
            else:
                emit_italic(part, fmt)

    def emit_italic(t: str, fmt: frozenset) -> None:
        pat = re.compile(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])|(?<![\w])_(?![\s_])(.+?)(?<![\s_])_(?![\w])")
        pos = 0
        for m in pat.finditer(t):
            if m.start() > pos:
                segs.append((t[pos:m.start()], fmt))
            segs.append((m.group(1) or m.group(2), fmt | {"i"}))
            pos = m.end()
        if pos < len(t):
            segs.append((t[pos:], fmt))

    for chunk in re.split(r"(`[^`]+`)", text):
        if chunk.startswith("`") and chunk.endswith("`") and len(chunk) > 2:
            segs.append((chunk[1:-1], frozenset({"c"})))
        elif chunk:
            emit(chunk, frozenset())
    return segs


def runs(text: str, base_bold: bool = False, size: int | None = None, color: str | None = None) -> str:
    out = []
    for t, fmt in parse_inline(text):
        for j, piece in enumerate(t.split("\n")):
            rpr = ""
            if "c" in fmt:
                rpr += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:shd w:val="clear" w:color="auto" w:fill="EFEFEF"/>'
            if base_bold or "b" in fmt:
                rpr += "<w:b/>"
            if "i" in fmt:
                rpr += "<w:i/>"
            if color:
                rpr += f'<w:color w:val="{color}"/>'
            if size:
                rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
            if j > 0:
                out.append("<w:r><w:br/></w:r>")
            if piece:
                out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(piece)}</w:t></w:r>')
    return "".join(out)


# ---------------------------------------------------------------- blocks
def para(text: str, style: str | None = None, *, bold: bool = False, jc: str | None = None, size: int | None = None,
         color: str | None = None, extra_ppr: str = "", keep_next: bool = False) -> str:
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        ppr += "<w:keepNext/>"
    ppr += extra_ppr
    if jc:
        ppr += f'<w:jc w:val="{jc}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{runs(text, bold, size, color)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(rows: list[list[str]]) -> str:
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    weights = []
    for c in range(n):
        lens = [len(re.sub(r"[*_`]", "", r[c])) for r in rows]
        w = max(min(max(lens[0], sum(lens[1:]) / max(len(lens) - 1, 1) if len(lens) > 1 else lens[0]), 46), 7)
        weights.append(w)
    total = sum(weights)
    widths = [max(int(TEXT_W * w / total), 720) for w in weights]
    widths[-1] += TEXT_W - sum(widths)
    b = '<w:top w:val="single" w:sz="4" w:color="BFBFBF"/><w:left w:val="single" w:sz="4" w:color="BFBFBF"/><w:bottom w:val="single" w:sz="4" w:color="BFBFBF"/><w:right w:val="single" w:sz="4" w:color="BFBFBF"/><w:insideH w:val="single" w:sz="4" w:color="BFBFBF"/><w:insideV w:val="single" w:sz="4" w:color="BFBFBF"/>'
    x = [f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_W}" w:type="dxa"/><w:tblBorders>{b}</w:tblBorders><w:tblLayout w:type="fixed"/>'
         '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr>'
         "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"]
    for ri, r in enumerate(rows):
        trpr = "<w:trPr><w:cantSplit/>" + ("<w:tblHeader/>" if ri == 0 else "") + "</w:trPr>"
        x.append(f"<w:tr>{trpr}")
        for ci, cell in enumerate(r):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{HONEY}"/>' if ri == 0 else (f'<w:shd w:val="clear" w:color="auto" w:fill="FFF8E7"/>' if ri % 2 == 0 else "")
            x.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shd}</w:tcPr>'
                     f'{para(cell, "TableText", bold=(ri == 0), color=DARK if ri == 0 else None)}</w:tc>')
        x.append("</w:tr>")
    x.append("</w:tbl>")
    return "".join(x) + '<w:p><w:pPr><w:spacing w:after="80"/></w:pPr></w:p>'


class Numbering:
    """Keeps one w:num per numbered list so each list restarts at 1."""
    def __init__(self) -> None:
        self.nums: list[int] = []

    def new_decimal(self) -> int:
        self.nums.append(len(self.nums) + 3)  # ids 1,2 are the bullet abstract/num
        return self.nums[-1]

    def xml(self) -> str:
        def lvl(i: int, fmt: str, txt: str, font: str = "") -> str:
            rf = f'<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:hint="default"/></w:rPr>' if font else ""
            return (f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{txt}"/><w:lvlJc w:val="left"/>'
                    f'<w:pPr><w:ind w:left="{360 + 360 * (i + 1)}" w:hanging="360"/></w:pPr>{rf}</w:lvl>')
        bullets = "".join(lvl(i, "bullet", ["•", "–", "▪"][i % 3], "") for i in range(6))
        decimals = "".join(lvl(i, "decimal" if i % 2 == 0 else "lowerLetter", f"%{i + 1}.") for i in range(6))
        nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
        nums += "".join(f'<w:num w:numId="{n}"><w:abstractNumId w:val="1"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>' for n in self.nums)
        return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f'<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>{bullets}</w:abstractNum>'
                f'<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>{decimals}</w:abstractNum>{nums}</w:numbering>')


def list_item(text: str, level: int, num_id: int) -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="{min(level, 5)}"/><w:numId w:val="{num_id}"/></w:numPr>'
            f'<w:spacing w:after="40"/></w:pPr>{runs(text)}</w:p>')


def code_block(lines: list[str]) -> str:
    out = []
    for i, ln in enumerate(lines or [""]):
        out.append('<w:p><w:pPr><w:pStyle w:val="Code"/>' + ("<w:keepNext/>" if i < len(lines) - 1 else "") + "</w:pPr>"
                   f'<w:r><w:t xml:space="preserve">{escape(ln)}</w:t></w:r></w:p>')
    return "".join(out) + '<w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>'


# ---------------------------------------------------------------- front matter
def split_front_matter(md: str) -> tuple[dict, str]:
    md = re.sub(r"^<!--.*?-->\s*", "", md, flags=re.S)
    m = re.match(r"^---\n(.*?)\n---\n", md, flags=re.S)
    if not m:
        return {}, md
    fm: dict = {}
    for line in m.group(1).splitlines():
        if re.match(r"^\S", line) and ":" in line:
            k, _, v = line.partition(":")
            v = v.split("  #")[0].strip().strip('"')
            if v:
                fm[k.strip()] = v
    return fm, md[m.end():]


def convert(md: str, cover: bool = True, title_override: str | None = None) -> tuple[str, Numbering, str]:
    fm, body = split_front_matter(md)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    lines = body.splitlines()
    numbering = Numbering()
    out: list[str] = []
    title = title_override or fm.get("project") or next((re.sub(r"^#\s+", "", l) for l in lines if l.startswith("# ")), "Product Requirements")
    headings: list[str] = []

    i = 0
    cur_num_id = None
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            cur_num_id = None if not (i < len(lines) and re.match(r"^\s*\d+[.)]\s", lines[i])) else cur_num_id
            continue
        if s.startswith("```"):
            j = i + 1
            block = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                block.append(lines[j].rstrip())
                j += 1
            out.append(code_block(block))
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            if lvl == 1:
                i += 1  # document title: shown on the cover
                if not cover:
                    out.append(para(txt, "Title"))
                continue
            style = {2: "Heading1", 3: "Heading2"}.get(lvl, "Heading3")
            if lvl == 2:
                headings.append(txt)
            out.append(para(txt, style, keep_next=True))
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            rows = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                if not re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[j]):
                    cells = re.split(r"(?<!\\)\|", lines[j].strip().strip("|"))
                    rows.append([c.strip().replace("\\|", "|") for c in cells])
                j += 1
            out.append(table(rows))
            i = j
            continue
        if re.match(r"^---+$|^\*\*\*+$", s):
            i += 1
            continue
        if s.startswith(">"):
            out.append(para(re.sub(r"^>\s?", "", s), "Quote"))
            i += 1
            continue
        m = re.match(r"^(\s*)([-*+])\s+(.*)$", line)
        if m:
            level = len(m.group(1).replace("\t", "  ")) // 2
            txt = m.group(3)
            txt = re.sub(r"^\[ \]\s*", "☐ ", txt)
            txt = re.sub(r"^\[[xX]\]\s*", "☑ ", txt)
            out.append(list_item(txt, level, 1))
            i += 1
            continue
        m = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", line)
        if m:
            if cur_num_id is None:
                cur_num_id = numbering.new_decimal()
            out.append(list_item(m.group(3), len(m.group(1).replace("\t", "  ")) // 2, cur_num_id))
            i += 1
            continue
        cur_num_id = None
        # paragraph (join soft-wrapped lines)
        buf = [s]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r"^(#{1,6}\s|\||```|>|\s*[-*+]\s|\s*\d+[.)]\s|---)", lines[j].strip() if not lines[j].startswith(("  ", "\t")) else "x"):
            buf.append(lines[j].strip())
            j += 1
        out.append(para(" ".join(buf), "BodyText"))
        i = j

    front = ""
    if cover:
        meta = [("Version", fm.get("version", "")), ("Status", fm.get("status", "")), ("Profile", fm.get("profile", "")),
                ("Date", fm.get("date", datetime.date.today().isoformat())), ("Owners", fm.get("owners", "").strip("[]").replace('"', ""))]
        meta = [(k, v) for k, v in meta if v]
        front += '<w:p><w:pPr><w:spacing w:before="2400"/></w:pPr></w:p>'
        front += para(title, "Title")
        front += para("Product Requirements & Technical Specification", "Subtitle")
        if meta:
            front += '<w:p><w:pPr><w:spacing w:after="240"/></w:pPr></w:p>'
            front += table([["Document control", "Value"]] + [[k, v] for k, v in meta])
        front += page_break()
    if headings:
        front += para("Contents", "Heading1")
        for h in headings:
            front += para(h, "BodyText", extra_ppr='<w:spacing w:after="40"/>')
        front += page_break()
    return front + "".join(out), numbering, title


# ---------------------------------------------------------------- package parts
NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


def styles_xml() -> str:
    def pstyle(sid: str, name: str, based: str | None, ppr: str, rpr: str, nxt: str | None = None, q: bool = True) -> str:
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
                + (f'<w:basedOn w:val="{based}"/>' if based else "")
                + (f'<w:next w:val="{nxt}"/>' if nxt else "") + ("<w:qFormat/>" if q else "")
                + f"<w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>")
    font = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri"/>'
    s = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         f'<w:styles {NS}><w:docDefaults><w:rPrDefault><w:rPr>{font}<w:sz w:val="21"/><w:szCs w:val="21"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
         '<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="264" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
         '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>')
    s += pstyle("BodyText", "Body Text", "Normal", "", "")
    s += pstyle("Title", "Title", "Normal", '<w:spacing w:after="120"/>', f'<w:b/><w:color w:val="{DARK}"/><w:sz w:val="60"/><w:szCs w:val="60"/>', "Normal")
    s += pstyle("Subtitle", "Subtitle", "Normal", '<w:spacing w:after="240"/>', '<w:color w:val="7A5A2E"/><w:sz w:val="30"/><w:szCs w:val="30"/>', "Normal")
    s += pstyle("Heading1", "heading 1", "Normal", f'<w:keepNext/><w:keepLines/><w:pBdr><w:bottom w:val="single" w:sz="8" w:space="2" w:color="{HONEY}"/></w:pBdr><w:spacing w:before="360" w:after="140"/><w:outlineLvl w:val="0"/>',
                f'<w:b/><w:color w:val="{DARK}"/><w:sz w:val="32"/><w:szCs w:val="32"/>', "BodyText")
    s += pstyle("Heading2", "heading 2", "Normal", '<w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="100"/><w:outlineLvl w:val="1"/>',
                f'<w:b/><w:color w:val="{DARK}"/><w:sz w:val="26"/><w:szCs w:val="26"/>', "BodyText")
    s += pstyle("Heading3", "heading 3", "Normal", '<w:keepNext/><w:keepLines/><w:spacing w:before="180" w:after="80"/><w:outlineLvl w:val="2"/>',
                '<w:b/><w:color w:val="7A5A2E"/><w:sz w:val="23"/><w:szCs w:val="23"/>', "BodyText")
    s += pstyle("TableText", "Table Text", "Normal", '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/>', '<w:sz w:val="18"/><w:szCs w:val="18"/>')
    s += pstyle("ListParagraph", "List Paragraph", "Normal", '<w:contextualSpacing/>', "")
    s += pstyle("Quote", "Quote", "Normal", '<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="F5A623"/></w:pBdr><w:ind w:left="360"/>', '<w:i/><w:color w:val="595959"/>')
    s += pstyle("Code", "Code", "Normal", f'<w:shd w:val="clear" w:color="auto" w:fill="{GREY}"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="120" w:right="120"/>',
                '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="17"/><w:szCs w:val="17"/>')
    s += pstyle("Footer", "footer", "Normal", '<w:jc w:val="center"/>', '<w:color w:val="7F7F7F"/><w:sz w:val="16"/><w:szCs w:val="16"/>', q=False)
    return s + "</w:styles>"


def footer_xml(title: str) -> str:
    def fld(instr: str) -> str:
        return (f'<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:ftr {NS}><w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr><w:r><w:t xml:space="preserve">{escape(title)}  ·  Page </w:t></w:r>{fld("PAGE")}'
            f'<w:r><w:t xml:space="preserve"> of </w:t></w:r>{fld("NUMPAGES")}</w:p></w:ftr>')


def build(md: str, out_path: Path, cover: bool, title_override: str | None) -> None:
    body, numbering, title = convert(md, cover, title_override)
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rId4"/><w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>')
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}{sect}</w:body></w:document>'
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
            '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
            '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>',
        "word/_rels/document.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
            '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/></Relationships>',
        "word/document.xml": document,
        "word/styles.xml": styles_xml(),
        "word/numbering.xml": numbering.xml(),
        "word/settings.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {NS}><w:defaultTabStop w:val="720"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>',
        "word/footer1.xml": footer_xml(title),
        "docProps/core.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(title)}</dc:title><dc:creator>Honey\'s Spec Harness</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>',
        "docProps/app.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Honey\'s Spec Harness</Application></Properties>',
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", parts.pop("[Content_Types].xml"))  # must be first
        for name, data in parts.items():
            z.writestr(name, data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--no-cover", action="store_true")
    ap.add_argument("--title")
    a = ap.parse_args()
    src = Path(a.src)
    if not src.exists():
        print(f"not found: {src}", file=sys.stderr)
        return 2
    build(src.read_text(encoding="utf-8"), Path(a.dst), not a.no_cover, a.title)
    print(f"wrote {a.dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
