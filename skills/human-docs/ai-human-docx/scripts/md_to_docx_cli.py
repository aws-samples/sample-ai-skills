#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = []
# ///
"""Convert one markdown file to a Microsoft Word (.docx) document.

Standard library only: the package is built as OOXML strings and zipped. With
`--template`, the styles, theme, font table, and page layout of a .dotx are
applied. Headers, footers, embedded media, custom list numbering, and document
settings are not carried over.

The input is a path to a `.md` file, or to a directory holding `draft.md`. No
name is resolved against anything else. The document is written beside the
input: a `draft.md` inside a `YYYY-MM-DD-<name>` directory becomes
`<name>.docx`, and any other `<stem>.md` becomes `<stem>.docx`. An existing
file at that path is replaced. The write goes through a temporary sibling file
and a rename, so a failed run leaves the output path exactly as it was.

Supported: headings (H1-H6), paragraphs, bold, italic, bold+italic,
strikethrough, inline code, hyperlinks, bullet and numbered lists (3 levels),
fenced code blocks, blockquotes, pipe tables, horizontal rules. YAML frontmatter
is removed from the body, and a scalar `title` becomes the document title. An
image becomes an italic `[Image: <alt>]` placeholder.

Usage:
  uv run md_to_docx_cli.py <path> [--template <file.dotx>] [--within <dir>]

On success, prints one line:
  Created <path> (<n> bytes); template: <path|none>; images replaced: <k>

Exit status: 0 when the document was written; 1 when nothing was written
because the input, the template, or the write failed; 2 when nothing was
written because the output lies outside `--within`, or on a usage error.
"""

import argparse
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET  # nosec B405 # parses only a template the user named; see extract_template
import zipfile
from io import BytesIO
from pathlib import Path

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

#: A document directory's creation-date prefix, removed from the output name.
DATED_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")

#: Characters XML 1.0 does not allow, even escaped.
_XML_INVALID = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class ConversionError(Exception):
    """A reason nothing was written, worded for the person who ran the command."""


# ═══════════════════════════════════════════════════════════════════
# XML SCAFFOLDING
# ═══════════════════════════════════════════════════════════════════

DEFAULT_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    # Document defaults: Times New Roman 10pt, single spacing, 6pt after
    '<w:docDefaults>'
    '<w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
    '<w:sz w:val="20"/><w:szCs w:val="20"/>'
    '</w:rPr></w:rPrDefault>'
    '<w:pPrDefault><w:pPr>'
    '<w:spacing w:after="120" w:line="240" w:lineRule="auto"/>'
    '</w:pPr></w:pPrDefault>'
    '</w:docDefaults>'
    # Normal
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:qFormat/></w:style>'
    # Heading 1 — 20pt bold
    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="120"/>'
    '<w:outlineLvl w:val="0"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>'
    # Heading 2 — 16pt bold
    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="80"/>'
    '<w:outlineLvl w:val="1"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>'
    # Heading 3 — 13pt bold
    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="160" w:after="80"/>'
    '<w:outlineLvl w:val="2"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>'
    # Heading 4 — 10pt bold
    '<w:style w:type="paragraph" w:styleId="Heading4">'
    '<w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="120" w:after="80"/>'
    '<w:outlineLvl w:val="3"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # Heading 5 — 10pt bold italic
    '<w:style w:type="paragraph" w:styleId="Heading5">'
    '<w:name w:val="heading 5"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="80" w:after="40"/>'
    '<w:outlineLvl w:val="4"/></w:pPr>'
    '<w:rPr><w:b/><w:bCs/><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # Heading 6 — 10pt italic
    '<w:style w:type="paragraph" w:styleId="Heading6">'
    '<w:name w:val="heading 6"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="80" w:after="40"/>'
    '<w:outlineLvl w:val="5"/></w:pPr>'
    '<w:rPr><w:i/><w:iCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:style>'
    # List Paragraph
    '<w:style w:type="paragraph" w:styleId="ListParagraph">'
    '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:ind w:left="720"/></w:pPr></w:style>'
    '</w:styles>'
)

ABSTRACT_NUMBERING = (
    # Bullets: bullet, hollow circle, dash (3 levels)
    '<w:abstractNum w:abstractNumId="0">'
    '<w:multiLevelType w:val="hybridMultilevel"/>'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x2022;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x25CB;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1440" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:hint="default"/></w:rPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
    '<w:lvlText w:val="&#x2013;"/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="2160" w:hanging="360"/></w:pPr>'
    '<w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:hint="default"/></w:rPr></w:lvl>'
    '</w:abstractNum>'
    # Decimal numbered: 1., a., i. (3 levels)
    '<w:abstractNum w:abstractNumId="1">'
    '<w:multiLevelType w:val="hybridMultilevel"/>'
    '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/>'
    '<w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="lowerLetter"/>'
    '<w:lvlText w:val="%2."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="1440" w:hanging="360"/></w:pPr></w:lvl>'
    '<w:lvl w:ilvl="2"><w:start w:val="1"/><w:numFmt w:val="lowerRoman"/>'
    '<w:lvlText w:val="%3."/><w:lvlJc w:val="left"/>'
    '<w:pPr><w:ind w:left="2160" w:hanging="360"/></w:pPr></w:lvl>'
    '</w:abstractNum>'
)

DEFAULT_SECT_PR = (
    '<w:sectPr>'
    '<w:pgSz w:w="12240" w:h="15840"/>'
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"'
    ' w:header="720" w:footer="720" w:gutter="0"/>'
    '</w:sectPr>'
)


# ═══════════════════════════════════════════════════════════════════
# XML HELPERS
# ═══════════════════════════════════════════════════════════════════

def esc(text):
    """Escape XML entities, & first, and drop characters XML cannot carry."""
    text = _XML_INVALID.sub("", text)
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wt(text):
    """Wrap text in <w:t>, adding xml:space='preserve' when needed."""
    escaped = esc(text)
    if text and (text[0] == " " or text[-1] == " "):
        return f'<w:t xml:space="preserve">{escaped}</w:t>'
    return f"<w:t>{escaped}</w:t>"


def make_run(text, bold=False, italic=False, code=False, strike=False):
    """Build a single <w:r> element with optional formatting."""
    rpr = []
    if code:
        rpr.append(
            '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
            '<w:shd w:val="clear" w:color="auto" w:fill="E8E8E8"/>'
        )
    if bold:
        rpr.append("<w:b/><w:bCs/>")
    if italic:
        rpr.append("<w:i/><w:iCs/>")
    if strike:
        rpr.append("<w:strike/>")
    rpr_xml = f'<w:rPr>{"".join(rpr)}</w:rPr>' if rpr else ""
    return f"<w:r>{rpr_xml}{wt(text)}</w:r>"


def image_placeholder(alt):
    """The text an image is replaced by: `[Image: <alt>]`, or `[Image]`."""
    return f"[Image: {alt}]" if alt.strip() else "[Image]"


# ═══════════════════════════════════════════════════════════════════
# INLINE PARSER
# ═══════════════════════════════════════════════════════════════════

# Images come before links, so `![alt](src)` never reaches the link branch. A
# linked image, `[![alt](src)](url)`, comes first of all, or the link branch
# would take `![alt` as its text. Plain text stops at every character that can
# open a construct, and `literal` keeps that character when no construct
# follows it: without it, `5 * 3` or `Hello!` would lose the `*` or the `!`.
INLINE = re.compile(
    r"\[!\[(?P<limg_alt>[^\]]*)\]\([^)]*\)\]\((?P<limg_url>[^)]+)\)"
    r"|!\[(?P<img_alt>[^\]]*)\]\([^)]*\)"
    r"|\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\)"
    r"|`(?P<code>[^`]+)`"
    r"|~~(?P<strike>.+?)~~"
    r"|\*\*\*(?P<bold_italic>.+?)\*\*\*"
    r"|\*\*(?P<bold>.+?)\*\*"
    r"|\*(?P<italic>.+?)\*"
    r"|(?P<text>[^`*~\[!]+)"
    r"|(?P<literal>[`*~\[!])"
)


class InlineParser:
    """Parses inline markdown into <w:r> XML, tracking hyperlink relationships
    and counting the images it replaced with placeholders."""

    def __init__(self):
        self.hyperlinks = []  # list of (rId, url)
        self.next_rel_id = 100  # start high to avoid collision with template rIds
        self.images = 0

    def hyperlink(self, url, text, italic=False):
        rid = f"rId{self.next_rel_id}"
        self.next_rel_id += 1
        self.hyperlinks.append((rid, url))
        slant = "<w:i/><w:iCs/>" if italic else ""
        return (
            f'<w:hyperlink r:id="{rid}">'
            f'<w:r><w:rPr>{slant}'
            f'<w:color w:val="0563C1"/><w:u w:val="single"/>'
            f'</w:rPr>{wt(text)}</w:r>'
            f'</w:hyperlink>'
        )

    def parse_inline(self, text):
        """Parse inline markdown into concatenated XML runs."""
        runs = []
        for m in INLINE.finditer(text):
            # The last group each alternative closes names that alternative.
            kind = m.lastgroup
            if kind == "limg_url":
                self.images += 1
                runs.append(self.hyperlink(
                    m.group("limg_url"), image_placeholder(m.group("limg_alt")), italic=True))
            elif kind == "img_alt":
                self.images += 1
                runs.append(make_run(image_placeholder(m.group("img_alt")), italic=True))
            elif kind == "link_url":
                runs.append(self.hyperlink(m.group("link_url"), m.group("link_text")))
            elif kind == "code":
                runs.append(make_run(m.group("code"), code=True))
            elif kind == "strike":
                runs.append(make_run(m.group("strike"), strike=True))
            elif kind == "bold_italic":
                runs.append(make_run(m.group("bold_italic"), bold=True, italic=True))
            elif kind == "bold":
                runs.append(make_run(m.group("bold"), bold=True))
            elif kind == "italic":
                runs.append(make_run(m.group("italic"), italic=True))
            else:
                runs.append(make_run(m.group(kind)))
        return "".join(runs)


# ═══════════════════════════════════════════════════════════════════
# TABLE PARSER
# ═══════════════════════════════════════════════════════════════════

def parse_table(lines, start, ip):
    """Parse a markdown table. Returns (xml_string, next_index) or (None, start)."""
    rows = []
    i = start
    while i < len(lines) and '|' in lines[i]:
        cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
        rows.append(cells)
        i += 1

    if len(rows) < 2:
        return None, start

    # Validate separator row (row index 1 must contain dashes/colons)
    if not all(re.match(r'^[-:]+$', c) for c in rows[1] if c):
        return None, start

    header, data = rows[0], rows[2:]
    nc = len(header)
    cw = 9360 // nc
    lw = 9360 - cw * (nc - 1)  # last column absorbs rounding remainder

    grid = ''.join(
        f'<w:gridCol w:w="{lw if j == nc - 1 else cw}"/>' for j in range(nc)
    )

    def mk_row(cells, hdr=False):
        tcs = []
        for j in range(nc):
            txt = cells[j] if j < len(cells) else ""
            w = lw if j == nc - 1 else cw
            r = ip.parse_inline(txt) if txt else ""
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if hdr else ''
            tcs.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr>'
                f'<w:p>{r}</w:p></w:tc>'
            )
        return f'<w:tr>{"".join(tcs)}</w:tr>'

    hdr_row = mk_row(header, hdr=True)
    data_xml = ''.join(mk_row(r) for r in data)

    return (
        '<w:tbl><w:tblPr>'
        '<w:tblW w:w="9360" w:type="dxa"/>'
        '<w:tblBorders>'
        '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
        '</w:tblBorders>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0"'
        ' w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
        '</w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>'
        f'{hdr_row}{data_xml}</w:tbl>'
    ), i


# ═══════════════════════════════════════════════════════════════════
# BLOCK PARSER
# ═══════════════════════════════════════════════════════════════════

def md_to_body(md_text, ip):
    """Convert Markdown text to XML body elements.
    Returns (list_of_xml_strings, max_num_id_used).

    A numbered list continues across blank lines. It ends at the first line that
    is neither blank nor a list item, or at a bullet item at nesting level 0, so
    the next numbered item starts a new list numbered from 1.
    """
    paras = []
    lines = md_text.split("\n")
    i = 0
    next_num_id = 2   # 1 = bullets, 2 = first numbered list, 3+ = restart
    in_num = False
    cur_num_id = 2

    while i < len(lines):
        line = lines[i]

        # ── Blank line: a numbered list continues past it ──
        if not line.strip():
            i += 1
            continue

        # ── Fenced code block ──
        if line.strip().startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # skip closing fence
            for cl in code:
                e = esc(cl) if cl.strip() else ""
                if cl and (cl[0] in " \t" or cl[-1] == " "):
                    t = f'<w:t xml:space="preserve">{e}</w:t>'
                elif not cl.strip():
                    t = '<w:t/>'
                else:
                    t = f'<w:t>{e}</w:t>'
                paras.append(
                    '<w:p><w:pPr>'
                    '<w:shd w:val="clear" w:color="auto" w:fill="F5F5F5"/>'
                    '<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
                    '<w:ind w:left="240" w:right="240"/>'
                    '</w:pPr><w:r><w:rPr>'
                    '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
                    f'<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>{t}</w:r></w:p>'
                )
            in_num = False
            continue

        # ── Horizontal rule ──
        if re.match(r'^(\s*)(---+|___+|\*\*\*+)\s*$', line):
            paras.append(
                '<w:p><w:pPr><w:pBdr>'
                '<w:bottom w:val="single" w:sz="6" w:space="1" w:color="999999"/>'
                '</w:pBdr></w:pPr></w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Heading ──
        hm = re.match(r'^(#{1,6})\s+(.+)$', line)
        if hm:
            lvl = len(hm.group(1))
            runs = ip.parse_inline(hm.group(2).strip())
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="Heading{lvl}"/></w:pPr>{runs}</w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Blockquote ──
        if line.startswith("> ") or line == ">":
            txt = line[2:] if line.startswith("> ") else ""
            runs = ip.parse_inline(txt) if txt else ""
            paras.append(
                '<w:p><w:pPr>'
                '<w:pBdr><w:left w:val="single" w:sz="12" w:space="8" w:color="AAAAAA"/></w:pBdr>'
                '<w:spacing w:before="120" w:after="120"/>'
                '<w:ind w:left="480"/>'
                f'</w:pPr>{runs}</w:p>'
            )
            in_num = False
            i += 1
            continue

        # ── Bullet list item ──
        bm = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if bm:
            lvl = min(len(bm.group(1)) // 2, 2)
            runs = ip.parse_inline(bm.group(2))
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
                f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="1"/></w:numPr>'
                f'</w:pPr>{runs}</w:p>'
            )
            # An indented bullet sits inside the numbered item above it.
            if lvl == 0:
                in_num = False
            i += 1
            continue

        # ── Numbered list item ──
        nm = re.match(r'^(\s*)\d+\.\s+(.+)$', line)
        if nm:
            if not in_num:
                cur_num_id = next_num_id
                next_num_id += 1
                in_num = True
            lvl = min(len(nm.group(1)) // 3, 2)
            runs = ip.parse_inline(nm.group(2))
            paras.append(
                f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
                f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="{cur_num_id}"/></w:numPr>'
                f'</w:pPr>{runs}</w:p>'
            )
            i += 1
            continue

        # ── Table ──
        if '|' in line and line.strip().startswith('|'):
            tbl, ni = parse_table(lines, i, ip)
            if tbl:
                paras.append(tbl)
                i = ni
                in_num = False
                continue

        # ── Normal paragraph (may span multiple lines) ──
        pl = []
        while (i < len(lines) and lines[i].strip()
               and not re.match(
                   r'^(#{1,6}\s|[-*+]\s|\d+\.\s|```|---+\s*$'
                   r'|\*\*\*+\s*$|___+\s*$|>|\|)', lines[i])):
            pl.append(lines[i].strip())
            i += 1
        if not pl:
            # A line no branch above takes, such as `>quote` or a lone `| a |`
            # row, is still text: it becomes a paragraph of its own.
            pl.append(lines[i].strip())
            i += 1
        runs = ip.parse_inline(" ".join(pl))
        paras.append(f"<w:p>{runs}</w:p>")
        in_num = False

    return paras, next_num_id - 1


# ═══════════════════════════════════════════════════════════════════
# FRONTMATTER
# ═══════════════════════════════════════════════════════════════════

def split_frontmatter(md_text):
    """Remove a leading YAML frontmatter block. Returns (body, title or None).

    A block exists only when line 1 is exactly `---` and a later line is exactly
    `---` or `...`; with no closing fence the text is returned unchanged. The
    title is the value of a `title:` line at column 0, with one layer of
    matching quotes removed. A value that is empty, or that opens a block or flow
    collection (`|`, `>`, `[`, `{`), is not a scalar and gives no title.
    """
    lines = md_text.split("\n")
    if not lines or lines[0] != "---":
        return md_text, None
    close = next((n for n in range(1, len(lines)) if lines[n] in ("---", "...")), None)
    if close is None:
        return md_text, None

    title = None
    for line in lines[1:close]:
        m = re.match(r"^title:(.*)$", line)
        if not m:
            continue
        value = m.group(1).strip()
        if not value or value[0] in "|>[{":
            break
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = re.sub(r"\s+#.*$", "", value)  # a YAML comment ends a plain scalar
        title = value.strip() or None
        break

    return "\n".join(lines[close + 1:]), title


# ═══════════════════════════════════════════════════════════════════
# PACKAGE PARTS
# ═══════════════════════════════════════════════════════════════════

def build_numbering_xml(max_num_id):
    """Build numbering.xml with bullet + numbered list definitions and restart entries."""
    max_num_id = max(max_num_id, 2)  # always include bullet and first number
    nums = [
        '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>',
        '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>',
    ]
    for nid in range(3, max_num_id + 1):
        nums.append(
            f'<w:num w:numId="{nid}"><w:abstractNumId w:val="1"/>'
            f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride>'
            f'</w:num>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + ABSTRACT_NUMBERING + ''.join(nums) + '</w:numbering>'
    )


def build_content_types(has_theme=False, has_font_table=False, has_core=False):
    """Build [Content_Types].xml dynamically based on included parts."""
    parts = [
        '<Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument'
        '.wordprocessingml.numbering+xml"/>',
    ]
    if has_theme:
        parts.append(
            '<Override PartName="/word/theme/theme1.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        )
    if has_font_table:
        parts.append(
            '<Override PartName="/word/fontTable.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.fontTable+xml"/>'
        )
    if has_core:
        parts.append(
            '<Override PartName="/docProps/core.xml"'
            ' ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels"'
        ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + ''.join(parts) + '</Types>'
    )


def build_package_rels(has_core=False):
    """Build _rels/.rels: the main document, plus core properties when present."""
    rels = [
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="word/document.xml"/>'
    ]
    if has_core:
        rels.append(
            '<Relationship Id="rId2"'
            ' Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"'
            ' Target="docProps/core.xml"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(rels) + '</Relationships>'
    )


def build_core_xml(title):
    """Build docProps/core.xml carrying the document title."""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties'
        ' xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:dcterms="http://purl.org/dc/terms/"'
        ' xmlns:dcmitype="http://purl.org/dc/dcmitype/"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{esc(title)}</dc:title>'
        '</cp:coreProperties>'
    )


def build_doc_rels(hyperlinks, has_theme=False, has_font_table=False):
    """Build word/_rels/document.xml.rels with base rels + optional template rels + hyperlinks."""
    rels = [
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"'
        ' Target="styles.xml"/>',
        '<Relationship Id="rId2"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering"'
        ' Target="numbering.xml"/>',
    ]
    if has_theme:
        rels.append(
            '<Relationship Id="rId3"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"'
            ' Target="theme/theme1.xml"/>'
        )
    if has_font_table:
        rels.append(
            '<Relationship Id="rId4"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"'
            ' Target="fontTable.xml"/>'
        )
    for rid, url in hyperlinks:
        rels.append(
            f'<Relationship Id="{rid}"'
            f' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"'
            f' Target="{esc(url)}" TargetMode="External"/>'
        )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(rels) + '</Relationships>'
    )


# ═══════════════════════════════════════════════════════════════════
# TEMPLATE EXTRACTOR
# ═══════════════════════════════════════════════════════════════════

def _references_relationships(element):
    """True if any attribute under `element` points through a relationship id.

    A template's relationships are not copied, so a part that points through one
    — a header reference, an embedded font, a theme image — would point at
    nothing in the output.
    """
    return any(
        name.startswith(f"{{{R_NS}}}") for node in element.iter() for name in node.attrib
    )


def extract_template(template_path):
    """The parts a .dotx contributes: styles, and when usable, theme, font table,
    and page layout.

    Raises ConversionError when the file is missing, is not a zip archive, lacks
    `word/styles.xml`, or holds an XML part this function reads that does not
    parse. Nothing has been written when it raises.
    """
    shown = str(template_path)
    if not template_path.is_file():
        raise ConversionError(f"template {shown}: no such file")
    ET.register_namespace('w', W_NS)
    ET.register_namespace('r', R_NS)
    try:
        with zipfile.ZipFile(template_path, 'r') as tz:
            names = set(tz.namelist())
            if 'word/styles.xml' not in names:
                raise ConversionError(f"template {shown}: could not be read: it has no word/styles.xml")
            members = {
                name: tz.read(name)
                for name in ('word/styles.xml', 'word/theme/theme1.xml',
                             'word/fontTable.xml', 'word/document.xml')
                if name in names
            }
    except zipfile.BadZipFile as e:
        raise ConversionError(f"template {shown}: could not be read: not a zip archive ({e})") from e
    except OSError as e:
        raise ConversionError(f"template {shown}: could not be read: {e}") from e

    # The XML is the template the user named on the command line, read from
    # their own disk. ElementTree resolves no external entity, and the expat
    # Python 3.14 bundles caps entity amplification.
    trees = {}
    for name, data in members.items():
        try:
            trees[name] = ET.fromstring(data)  # nosec B314 # see the comment above
        except ET.ParseError as e:
            raise ConversionError(f"template {shown}: could not be read: {name} does not parse ({e})") from e

    parts = {'styles': members['word/styles.xml']}
    if 'word/theme/theme1.xml' in trees and not _references_relationships(trees['word/theme/theme1.xml']):
        parts['theme'] = members['word/theme/theme1.xml']
    if 'word/fontTable.xml' in trees and not _references_relationships(trees['word/fontTable.xml']):
        parts['font_table'] = members['word/fontTable.xml']
    if 'word/document.xml' in trees:
        sect = trees['word/document.xml'].find(f'.//{{{W_NS}}}sectPr')
        if sect is not None:
            # Header and footer references point through relationships this
            # package does not carry; headers and footers are not carried over.
            for child in [c for c in sect if _references_relationships(c)]:
                sect.remove(child)
            parts['sect_pr'] = ET.tostring(sect, encoding='unicode')
    return parts


# ═══════════════════════════════════════════════════════════════════
# DOCX ASSEMBLER
# ═══════════════════════════════════════════════════════════════════

def build_docx(md_text, tmpl=None):
    """Convert Markdown to .docx bytes, with an extracted template's parts if
    given. Returns (bytes, number of images replaced by placeholders)."""
    tmpl = tmpl or {}
    has_theme = 'theme' in tmpl
    has_ft = 'font_table' in tmpl

    body_md, title = split_frontmatter(md_text)
    has_core = title is not None

    ip = InlineParser()
    paras, max_num_id = md_to_body(body_md, ip)

    sect_pr = tmpl.get('sect_pr', DEFAULT_SECT_PR)
    body = "\n".join(paras)
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<w:body>{body}{sect_pr}</w:body></w:document>'
    )

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', build_content_types(has_theme, has_ft, has_core))
        zf.writestr('_rels/.rels', build_package_rels(has_core))
        zf.writestr('word/_rels/document.xml.rels',
                     build_doc_rels(ip.hyperlinks, has_theme, has_ft))
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/styles.xml', tmpl.get('styles', DEFAULT_STYLES))
        zf.writestr('word/numbering.xml', build_numbering_xml(max_num_id))
        if has_theme:
            zf.writestr('word/theme/theme1.xml', tmpl['theme'])
        if has_ft:
            zf.writestr('word/fontTable.xml', tmpl['font_table'])
        if has_core:
            zf.writestr('docProps/core.xml', build_core_xml(title))
    return buf.getvalue(), ip.images


# ═══════════════════════════════════════════════════════════════════
# INPUT, OUTPUT, AND THE WRITE
# ═══════════════════════════════════════════════════════════════════

def resolve_input(argument):
    """The one markdown file `argument` names: a `.md` file, or a directory's
    `draft.md`. Nothing else is accepted and nothing is searched for."""
    if not argument:
        raise ConversionError(
            "no input given: pass a path to a .md file, or to a directory that holds draft.md"
        )
    path = Path(argument)
    if path.is_dir():
        draft = path / "draft.md"
        if not draft.is_file():
            raise ConversionError(
                f"{draft} does not exist. A path to a markdown file is also accepted"
            )
        return draft
    if not path.exists():
        raise ConversionError(
            f"{path} does not exist: pass a path to a .md file, or to a directory that holds draft.md"
        )
    if not path.is_file():
        raise ConversionError(f"{path} is not a regular file")
    if path.suffix != ".md":
        raise ConversionError(f"{path} is not a markdown file: the input must end in .md")
    return path


def output_path(source):
    """Where the document for `source` goes: beside it, under a reader-facing name.

    A `draft.md` in a `YYYY-MM-DD-<name>` directory becomes `<name>.docx`. Any
    other `<stem>.md` becomes `<stem>.docx`. The directory name is read from the
    resolved path, so `.` as the directory still finds its name.
    """
    if source.name == "draft.md":
        dated = DATED_DIR.match(source.resolve().parent.name)
        if dated:
            return source.parent / f"{dated.group(1)}.docx"
    return source.with_suffix(".docx")


def outside(target, root):
    """The resolved output path if it lies outside `root`, else None.

    The output's directory is resolved, symlinks included, and the file name is
    kept, because `os.replace` replaces the directory entry itself.
    """
    if not root.is_dir():
        raise ConversionError(f"--within {root}: not a directory")
    resolved = target.parent.resolve() / target.name
    return None if resolved.is_relative_to(root.resolve()) else resolved


def read_markdown(source):
    try:
        return source.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        raise ConversionError(f"{source} is not UTF-8 text ({e})") from e
    except OSError as e:
        raise ConversionError(f"{source} could not be read: {e}") from e


def write_atomically(target, data):
    """Write `data` to `target` through a temporary sibling and `os.replace`.

    The sibling is in the target's own directory so the rename stays on one
    filesystem and is atomic. It is removed on every exit path, so a failure
    leaves the target exactly as it was, or still absent.
    """
    try:
        fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".", suffix=".docx.tmp")
    except OSError as e:
        raise ConversionError(f"could not write {target}: {e}") from e
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        # mkstemp creates the file 0600; give the document the mode an ordinary
        # write would have.
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)
        os.replace(tmp, target)
    except BaseException as e:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        if isinstance(e, OSError):
            raise ConversionError(f"could not write {target}: {e}") from e
        raise


# ═══════════════════════════════════════════════════════════════════
# CLI ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="md_to_docx_cli.py",
        description="Convert one markdown file to a Word document written beside it.",
    )
    parser.add_argument(
        "path", nargs="?",
        help="a .md file, or a directory that holds draft.md",
    )
    parser.add_argument(
        "--template", metavar="FILE.dotx",
        help="apply this template's styles, theme, font table, and page layout",
    )
    parser.add_argument(
        "--within", metavar="DIR",
        help="refuse, with exit status 2, an output path that does not resolve under DIR",
    )
    args = parser.parse_args(argv)

    try:
        source = resolve_input(args.path)
        target = output_path(source)
        if args.within is not None:
            escaped = outside(target, Path(args.within))
            if escaped is not None:
                print(
                    f"refused: the output {escaped} lies outside {Path(args.within).resolve()};"
                    " nothing was written",
                    file=sys.stderr,
                )
                return 2
        tmpl = extract_template(Path(args.template)) if args.template else None
        data, images = build_docx(read_markdown(source), tmpl)
        replaced = target.exists()
        write_atomically(target, data)
    except ConversionError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(
        f"Created {target} ({len(data)} bytes); template: {args.template or 'none'};"
        f" images replaced: {images}"
    )
    if replaced:
        print(f"Replaced the earlier {target}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
