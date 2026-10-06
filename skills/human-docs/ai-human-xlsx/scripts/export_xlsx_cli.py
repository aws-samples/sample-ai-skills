#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = ["XlsxWriter==3.2.9"]
# ///
"""Export a markdown file, or a folder of markdown files, to one .xlsx workbook.

Two subcommands, so a person can confirm the mapping between them:

  plan <input> [--output PATH] [--save FILE]
      Read the input and print the plan as JSON: the mode, the output path and
      whether a file is already there, every sheet with its source, heading,
      name and whether that name was suffixed, every image and link with its
      resolution, and every warning. Writes nothing, unless --save names a file
      to receive a copy of the plan.

  write --plan FILE
      Validate the plan, rebuild the workbook from the input it names, and
      write it to the plan's output. Prints `wrote: <path>`, `sheets: <n>`,
      and one `warning: ...` line per warning.

A plan may be edited between the two. `write` honours three fields and nothing
else: each sheet's `name`, `output`, and `overwrite` (false by default, so an
existing workbook is never replaced unless the plan says so). Everything else
is recomputed from the input, and a plan that no longer matches it is refused.

The workbook is built at a temporary path and moved into place only once it is
complete, so the output path either receives the whole workbook or is left as
it was. The input is only ever read.

Exit status: 0 on success, 1 on a refusal, and 2 on a usage error. Either
failure prints a line starting `export_xlsx_cli.py: error:` on stderr, so a
failure without one came from `uv` before this script ran.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from urllib.parse import unquote

import xlsxwriter
from xlsxwriter.image import Image

PLAN_VERSION = 1

#: Excel's limits. Each is Excel's own, not XlsxWriter's.
MAX_ROWS = 1_048_576
MAX_CELL_CHARS = 32_767
MAX_SHEET_NAME = 31
MAX_ROW_HEIGHT_PT = 409
#: XlsxWriter ignores a longer URL and writes nothing in its cell.
MAX_URL_CHARS = 2_079
#: Excel treats integers past 15 significant digits as approximate.
MAX_DIGITS = 15

FORBIDDEN_IN_SHEET_NAME = "[]:*?/\\"
#: Excel reserves this sheet name, whatever its case.
RESERVED_SHEET_NAME = "history"

#: Column A holds one prose block per row; B onward hold extra links.
PROSE_WIDTH = 100
LINK_WIDTH = 40
TABLE_MIN_WIDTH = 8
TABLE_MAX_WIDTH = 60
#: XlsxWriter's conversion from a column width in characters to pixels.
PROSE_WIDTH_PX = int(PROSE_WIDTH * 7 + 0.5) + 5


class Refusal(Exception):
    """A reason to stop with exit status 1 and nothing written."""


# --- the parser -------------------------------------------------------------


@dataclass
class Block:
    """One block of the markdown subset: heading, paragraph, item, code, quote, table."""

    kind: str
    line: int
    text: str = ""
    level: int = 0
    header: list = field(default_factory=list)
    rows: list = field(default_factory=list)


_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_ITEM = re.compile(r"^([ \t]*)([-*+]|[0-9]{1,9}[.)])[ \t]+(.*)$")
_QUOTE = re.compile(r"^ {0,3}> ?(.*)$")
_DELIMITER = re.compile(r"^ *\|? *:?-+:? *(\| *:?-+:? *)*\|? *$")


def split_cells(line: str) -> list:
    """The cells of one GFM table row: split on unescaped `|`, outer pipes dropped."""
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    cells, current, i = [], "", 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] == "|":
            current += "|"
            i += 2
            continue
        if text[i] == "|":
            cells.append(current.strip())
            current = ""
        else:
            current += text[i]
        i += 1
    cells.append(current.strip())
    return cells


def _starts_block(line: str) -> bool:
    return bool(_HEADING.match(line) or _FENCE.match(line) or _ITEM.match(line) or _QUOTE.match(line))


def parse(text: str) -> list:
    """The blocks of `text`, in order. Anything outside the subset is kept as text.

    A leading YAML front matter block is document metadata, not content, and is
    skipped. Setext headings, HTML, and thematic breaks become paragraph text.
    """
    lines = text.expandtabs(4).splitlines()
    blocks = []
    i = 0
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() in ("---", "..."):
                i = end + 1
                break
    indents = []  # the list nesting stack: one marker indent per open level

    while i < len(lines):
        line = lines[i]
        number = i + 1
        if not line.strip():
            i += 1
            continue

        if m := _FENCE.match(line):
            fence = m.group(1)
            body = []
            i += 1
            while i < len(lines):
                close = lines[i].strip()
                if close.startswith(fence[0] * len(fence)) and not close.strip(fence[0]):
                    i += 1
                    break
                body.append(lines[i])
                i += 1
            blocks.append(Block("code", number, "\n".join(body)))
            indents = []
            continue

        if m := _HEADING.match(line):
            blocks.append(Block("heading", number, (m.group(2) or "").strip(), level=len(m.group(1))))
            indents = []
            i += 1
            continue

        if "|" in line and i + 1 < len(lines) and _DELIMITER.match(lines[i + 1]) and "|" in lines[i + 1]:
            header = split_cells(line)
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                cells = split_cells(lines[i])
                rows.append((cells + [""] * len(header))[: len(header)])
                i += 1
            blocks.append(Block("table", number, header=header, rows=rows))
            indents = []
            continue

        if m := _ITEM.match(line):
            indent = len(m.group(1))
            while indents and indents[-1] > indent:
                indents.pop()
            if not indents or indents[-1] < indent:
                indents.append(indent)
            parts = [f"{m.group(2)} {m.group(3).strip()}"]
            i += 1
            while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
                parts.append(lines[i].strip())
                i += 1
            blocks.append(Block("item", number, " ".join(parts), level=len(indents) - 1))
            continue

        if _QUOTE.match(line):
            paragraphs, current = [], []
            while i < len(lines) and (m := _QUOTE.match(lines[i])):
                if m.group(1).strip():
                    current.append(m.group(1).strip())
                elif current:
                    paragraphs.append(" ".join(current))
                    current = []
                i += 1
            if current:
                paragraphs.append(" ".join(current))
            blocks.append(Block("quote", number, "\n".join(paragraphs)))
            indents = []
            continue

        parts = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not _starts_block(lines[i]):
            if "|" in lines[i] and i + 1 < len(lines) and _DELIMITER.match(lines[i + 1]):
                break
            parts.append(lines[i].strip())
            i += 1
        blocks.append(Block("paragraph", number, " ".join(parts)))
        indents = []
    return blocks


# --- inline text: links and images ----------------------------------------

_CODE_SPAN = r"`[^`\n]*`"
_DESTINATION = r"\s*(<[^>\n]*>|[^\s)]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
_IMAGES = re.compile(rf"({_CODE_SPAN})|!\[([^\]]*)\]\({_DESTINATION}")
_LINKS = re.compile(rf"({_CODE_SPAN})|\[([^\]]+)\]\({_DESTINATION}|<((?:https?|ftp)://[^\s>]+|mailto:[^\s>]+)>")
_EXTERNAL = re.compile(r"^(?:(?:https?|ftp)://|mailto:)", re.IGNORECASE)
_REMOTE = re.compile(r"^(?:https?:)?//", re.IGNORECASE)
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


@dataclass
class Link:
    text: str
    target: str
    resolution: str  # external | sheet | text
    url: str = ""
    sheet_id: str = ""


@dataclass
class ImageRef:
    alt: str
    path: str
    status: str  # ok | missing | remote | unsupported
    reason: str = ""
    file: Path | None = None
    width: float = 0.0
    height: float = 0.0


def _destination(raw: str) -> str:
    return raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw


def classify_image(alt: str, raw: str, source: Path) -> ImageRef:
    """Whether a referenced image can be embedded, and why not when it cannot.

    Only a path relative to the markdown file is embedded. Nothing is fetched.
    """
    path = _destination(raw)
    if _REMOTE.match(path):
        return ImageRef(alt, path, "remote", f"Image {path} is remote and was not fetched.")
    if _SCHEME.match(path) or Path(unquote(path)).is_absolute():
        return ImageRef(alt, path, "unsupported", f"Image {path} is not a path relative to the markdown file.")
    file = source.parent / unquote(path)
    if not file.is_file():
        return ImageRef(alt, path, "missing", f"Image {path} was not found.")
    with file.open("rb") as handle:
        magic = handle.read(8)
    if not (magic.startswith(b"\x89PNG\r\n\x1a\n") or magic.startswith(b"\xff\xd8") or magic.startswith(b"GIF8")):
        return ImageRef(alt, path, "unsupported", f"Image {path} is not a PNG, JPEG, or GIF.")
    try:
        image = Image(str(file))
        width = image.width * 96 / (image.x_dpi or 96)
        height = image.height * 96 / (image.y_dpi or 96)
    except Exception:  # a truncated or corrupt file with a valid signature
        return ImageRef(alt, path, "unsupported", f"Image {path} could not be read.")
    if not (width and height):
        return ImageRef(alt, path, "unsupported", f"Image {path} could not be read.")
    return ImageRef(alt, path, "ok", file=file, width=width, height=height)


def classify_link(text: str, raw: str, source: Path, exported: dict) -> Link:
    """A URL is external; a `.md` file this run exports is a sheet; anything else is text.

    A URL longer than XlsxWriter accepts is text too, so it is shown rather than
    dropped.
    """
    target = _destination(raw)
    if _EXTERNAL.match(target):
        if len(target) > MAX_URL_CHARS:
            return Link(text, target, "text")
        return Link(text, target, "external", url=target)
    path = target.split("#", 1)[0].split("?", 1)[0]
    if path.lower().endswith(".md") and not _SCHEME.match(path):
        sheet_id = exported.get((source.parent / unquote(path)).resolve())
        if sheet_id:
            return Link(text, target, "sheet", sheet_id=sheet_id)
    return Link(text, target, "text")


@dataclass
class Inline:
    text: str
    links: list
    images: list


def inline(text: str, source: Path, exported: dict, embed: bool = True) -> Inline:
    """`text` with image and link syntax replaced by display text, plus what was replaced.

    An image shows as its alt text, and with `embed` is also classified for
    embedding. A link that stays text shows its target in parentheses, so nothing
    is lost. Code spans are left alone.
    """
    images, links = [], []

    def image(m):
        if m.group(1):
            return m.group(1)
        if embed:
            images.append(classify_image(m.group(2), m.group(3), source))
        return m.group(2)

    def link(m):
        if m.group(1):
            return m.group(1)
        if m.group(4):
            found = classify_link(m.group(4), m.group(4), source, exported)
        else:
            found = classify_link(m.group(2), m.group(3), source, exported)
        links.append(found)
        return found.text if found.resolution != "text" else f"{found.text} ({found.target})"

    text = _LINKS.sub(link, _IMAGES.sub(image, text))
    return Inline(text, links, images)


# --- table cells ------------------------------------------------------------

_INT = r"0|-?[1-9][0-9]*"
_DECIMAL = r"-?(?:0|[1-9][0-9]*)\.[0-9]+"
_GROUPED = r"-?[1-9][0-9]{0,2}(?:,[0-9]{3})+(?:\.[0-9]+)?"
_NUMBER = re.compile(rf"^(?:(?P<grouped>{_GROUPED})|(?P<decimal>{_DECIMAL})|(?P<int>{_INT}))(?P<pct>%?)$")
_DATE = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})$")


@dataclass
class Cell:
    kind: str  # text | number | date | boolean | link
    value: object
    num_format: str = ""
    link: Link | None = None
    links: list = field(default_factory=list)


def type_cell(text: str) -> Cell:
    """The cell `text` becomes. Text unless the whole cell is unambiguously a value.

    A leading zero, a currency symbol, a decimal comma, a backticked value, and a
    number past Excel's 15 significant digits all stay text: a wrong guess
    silently changes the value, and a text cell is still readable.
    """
    if m := _NUMBER.match(text):
        digits = re.sub(r"[^0-9]", "", text).lstrip("0")
        if len(digits) <= MAX_DIGITS:
            plain = text.rstrip("%").replace(",", "")
            places = "0" * len(plain.partition(".")[2])
            pattern = ("#,##0" if m.group("grouped") else "0") + (f".{places}" if places else "")
            if m.group("pct"):
                return Cell("number", float(Decimal(plain) / 100), pattern + "%")
            value = int(plain) if not places else float(Decimal(plain))
            return Cell("number", value, pattern if pattern != "0" else "")
    if m := _DATE.match(text):
        try:
            date = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return Cell("text", text)
        if date.year >= 1900:
            return Cell("date", date, "yyyy-mm-dd")
    if text.lower() in ("true", "false"):
        return Cell("boolean", text.lower() == "true")
    return Cell("text", text)


# --- the model: sheets and their rows ---------------------------------------


@dataclass
class Row:
    """One prose row of column A, an image row, or a table and the rows under it."""

    kind: str  # heading | text | quote | code | image | warning | table
    line: int
    text: str = ""
    links: list = field(default_factory=list)
    image: ImageRef | None = None
    header: list = field(default_factory=list)
    cells: list = field(default_factory=list)

    @property
    def height(self) -> int:
        """Rows occupied: a table takes its header and at least one data row."""
        return 1 + max(1, len(self.cells)) if self.kind == "table" else 1


@dataclass
class Sheet:
    id: str
    base: str
    source: str
    heading: str
    kind: str  # rows | table | index
    blocks: list = field(default_factory=list)
    rows: list = field(default_factory=list)


@dataclass
class Model:
    mode: str
    input: Path
    output: Path
    files: list
    sheets: list
    has_readme: bool | None


def plain(text: str) -> str:
    """`text` with link and image syntax reduced to the text a reader sees."""
    text = _IMAGES.sub(lambda m: m.group(1) or m.group(2), text)
    return _LINKS.sub(lambda m: m.group(1) or m.group(2) or m.group(4), text)


def split_sections(blocks: list) -> list:
    """Section-per-sheet: one sheet per H2, after one for any content before the first.

    The first sheet is named from the file's H1, or `Overview`. A file whose only
    content before its first H2 is that H1 gets no first sheet.
    """
    starts = [i for i, b in enumerate(blocks) if b.kind == "heading" and b.level == 2]
    preamble = blocks[: starts[0]] if starts else blocks
    title = next((b for b in preamble if b.kind == "heading" and b.level == 1), None)
    sheets = []
    if not starts or any(b is not title for b in preamble):
        heading = title.text if title else ""
        sheets.append(Sheet("", plain(heading) or "Overview", "", heading, "rows", preamble))
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(blocks)
        sheets.append(Sheet("", plain(blocks[start].text), "", blocks[start].text, "rows", blocks[start:end]))
    return sheets


def split_tables(blocks: list) -> list:
    """Table-per-sheet: each table on its own sheet, named from the nearest heading
    above it, and the prose on one `Notes` sheet when there is any besides headings."""
    sheets, notes, nearest = [], [], None
    for block in blocks:
        if block.kind == "table":
            heading = nearest.text if nearest else ""
            sheets.append(Sheet("", plain(heading) or "Table", "", heading, "table", [block]))
            continue
        if block.kind == "heading":
            nearest = block
        notes.append(block)
    if any(b.kind != "heading" for b in notes):
        sheets.append(Sheet("", "Notes", "", "", "rows", notes))
    return sheets


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as err:
        raise Refusal(f"{path} is not UTF-8 text ({err.reason} at byte {err.start})") from None


def table_row(block: Block, source: Path, exported: dict) -> Row:
    header, seen = [], set()
    for j, raw in enumerate(block.header):
        name = (inline(raw, source, exported, embed=False).text or f"Column {j + 1}")[:255]
        base, n = name, 1
        while name.lower() in seen:
            n += 1
            name = f"{base[: 255 - len(str(n)) - 1]}-{n}"
        seen.add(name.lower())
        header.append(name)
    cells = []
    for raw_row in block.rows:
        row = []
        for raw in raw_row:
            found = inline(raw, source, exported, embed=False)
            live = [link for link in found.links if link.resolution != "text"]
            if len(live) == 1:
                row.append(Cell("link", found.text, link=live[0]))
            elif found.links or found.text != raw:
                row.append(Cell("text", found.text))
            else:
                row.append(type_cell(raw))
            row[-1].links = found.links
        cells.append(row)
    return Row("table", block.line, header=header, cells=cells)


def render(blocks: list, source: Path, exported: dict) -> list:
    """The rows `blocks` become: one per block, then one per image it references."""
    rows = []
    for block in blocks:
        if block.kind == "table":
            rows.append(table_row(block, source, exported))
            continue
        if block.kind == "code":
            rows.append(Row("code", block.line, block.text))
            continue
        found = inline(block.text, source, exported)
        kind = {"heading": "heading", "quote": "quote"}.get(block.kind, "text")
        text = ("  " * block.level + found.text) if block.kind == "item" else found.text
        if not found.images or _IMAGES.sub(lambda m: m.group(1) or "", block.text).strip():
            rows.append(Row(kind, block.line, text, links=found.links))
        for image in found.images:
            rows.append(Row("image" if image.status == "ok" else "warning", block.line, image.reason, image=image))
    return rows


def build(input_path: Path, output: Path | None) -> Model:
    """Everything `plan` reports and `write` writes, computed from the input alone."""
    source = input_path.expanduser().resolve()
    if source.is_dir():
        found = sorted(
            (p for p in source.iterdir() if p.is_file() and p.suffix.lower() == ".md" and not p.name.startswith(".")),
            key=lambda p: p.name,
        )
        readme = next((p for p in found if p.name.lower() == "readme.md"), None)
        files = [p for p in found if p is not readme]
        if not found:
            raise Refusal(f"no .md file directly in {source}")
        mode, root, default_output = "folder", source, source / f"{source.name}.xlsx"
    elif source.is_file():
        if source.suffix.lower() != ".md":
            raise Refusal(f"{source} is not a .md file")
        readme, files = None, [source]
        mode, root, default_output = "file", source.parent, source.with_suffix(".xlsx")
    else:
        raise Refusal(f"no file or folder at {source}")

    target = output.expanduser().resolve() if output else default_output
    if target.suffix.lower() != ".xlsx":
        raise Refusal(f"the output {target} does not end in .xlsx")
    if not target.parent.is_dir():
        raise Refusal(f"the output folder {target.parent} does not exist, and this script never creates one")

    sheets, described, exported, parsed = [], [], {}, {}
    if mode == "folder":
        sheets.append(Sheet("index", "Index", readme.name if readme else "", "", "index"))
        described.append({"source": readme.name if readme else "", "mapping": "index"})
        if readme:
            exported[readme.resolve()] = "index"
    for path in files:
        rel = path.relative_to(root).as_posix()
        blocks = parse(read_markdown(path))
        mapping = "table-per-sheet" if any(b.kind == "table" for b in blocks) else "section-per-sheet"
        mapped = (split_tables if mapping == "table-per-sheet" else split_sections)(blocks)
        for n, sheet in enumerate(mapped, start=1):
            sheet.id, sheet.source = f"{rel}#{n}", rel
        exported[path.resolve()] = mapped[0].id
        parsed[rel] = path
        described.append({"source": rel, "mapping": mapping})
        sheets.extend(mapped)

    for sheet in sheets:
        if sheet.kind == "index":
            if readme:
                sheet.rows = render(parse(read_markdown(readme)), readme, exported)
            sheet.rows.append(Row("heading", 0, "Files"))
            for path in files:
                rel = path.relative_to(root).as_posix()
                link = Link(rel, rel, "sheet", sheet_id=exported[path.resolve()])
                sheet.rows.append(Row("text", 0, rel, links=[link]))
        else:
            sheet.rows = render(sheet.blocks, parsed[sheet.source], exported)
        if sum(row.height for row in sheet.rows) > MAX_ROWS:
            raise Refusal(f"{sheet.source or 'the Index'} needs more than Excel's {MAX_ROWS:,} rows on one sheet")
    return Model(mode, source, target, described, sheets, (readme is not None) if mode == "folder" else None)


# --- sheet names --------------------------------------------------------------


def sanitize(raw: str) -> str:
    """A legal sheet name: forbidden characters become `-`, then cut to 31 characters."""
    name = " ".join("".join("-" if c in FORBIDDEN_IN_SHEET_NAME else c for c in raw).split())
    return name.strip(" '")[:MAX_SHEET_NAME].strip(" '") or "Sheet"


def unique_names(bases: list) -> list:
    """`(name, suffixed)` per base: a later collision gets `-2`, `-3`, … within 31
    characters. Excel compares sheet names without case, and reserves `History`."""
    used, out = {RESERVED_SHEET_NAME}, []
    for base in bases:
        name, n = base, 1
        while name.lower() in used:
            n += 1
            suffix = f"-{n}"
            name = base[: MAX_SHEET_NAME - len(suffix)].rstrip(" '") + suffix
        used.add(name.lower())
        out.append((name, n > 1))
    return out


def name_problems(names: list) -> list:
    problems, used = [], {RESERVED_SHEET_NAME}
    for name in names:
        if not isinstance(name, str) or not name.strip():
            problems.append(f"sheet name {name!r} is empty or not a string")
            continue
        if len(name) > MAX_SHEET_NAME:
            problems.append(f"sheet name {name!r} is over {MAX_SHEET_NAME} characters")
        if any(c in FORBIDDEN_IN_SHEET_NAME for c in name):
            problems.append(f"sheet name {name!r} contains one of {FORBIDDEN_IN_SHEET_NAME}")
        if name.startswith("'") or name.endswith("'"):
            problems.append(f"sheet name {name!r} starts or ends with an apostrophe")
        if name.lower() in used:
            problems.append(f"sheet name {name!r} is used twice, ignoring case, or is reserved by Excel")
        used.add(name.lower())
    return problems


# --- plan ---------------------------------------------------------------------


def cell_ref(row: int, col: int) -> str:
    letters, col = "", col + 1
    while col:
        col, rest = divmod(col - 1, 26)
        letters = chr(65 + rest) + letters
    return f"{letters}{row + 1}"


def walk_rows(sheet: Sheet):
    """`(row, top)` for each row of a sheet, `top` being its first 0-based row."""
    top = 0
    for row in sheet.rows:
        yield row, top
        top += row.height


def report(model: Model, names: list) -> tuple:
    """`(images, links, warnings)` as the plan lists them, under the given names."""
    by_id = {sheet.id: name for sheet, name in zip(model.sheets, names)}
    images, links, warnings = [], [], []
    for sheet, name in zip(model.sheets, names):
        for row, top in walk_rows(sheet):
            found = [(link, cell_ref(top, 0)) for link in row.links]
            texts = [(row.text, cell_ref(top, 0))] if row.kind != "table" else []
            for r, cells in enumerate(row.cells):
                for c, cell in enumerate(cells):
                    found += [(link, cell_ref(top + 1 + r, c)) for link in cell.links]
                    if cell.kind in ("text", "link"):
                        texts.append((str(cell.value), cell_ref(top + 1 + r, c)))
            where = f" ({sheet.source}:{row.line})" if row.line else ""
            if row.image:
                images.append({"source": sheet.source, "line": row.line, "path": row.image.path, "status": row.image.status, "sheet": name, "cell": cell_ref(top, 0)})
                if row.image.status != "ok":
                    warnings.append(f"{name}!{cell_ref(top, 0)}: {row.image.reason}{where}")
            for link, ref in found:
                entry = {"source": sheet.source, "line": row.line, "target": link.target, "resolution": link.resolution, "sheet": name, "cell": ref}
                if link.sheet_id:
                    entry["to"] = by_id[link.sheet_id]
                links.append(entry)
                if len(link.target) > MAX_URL_CHARS and _EXTERNAL.match(link.target):
                    warnings.append(f"{name}!{ref}: a link target is over {MAX_URL_CHARS:,} characters, so it is kept as text{where}")
            for text, ref in texts:
                if len(text) > MAX_CELL_CHARS:
                    warnings.append(f"{name}!{ref}: cut from {len(text):,} to {MAX_CELL_CHARS:,} characters, Excel's limit{where}")
    return images, links, warnings


def plan_of(model: Model) -> dict:
    named = unique_names([sanitize(sheet.base) for sheet in model.sheets])
    names = [name for name, _ in named]
    images, links, warnings = report(model, names)
    plan = {
        "plan_version": PLAN_VERSION,
        "input": str(model.input),
        "mode": model.mode,
        "output": str(model.output),
        "output_exists": model.output.exists(),
        "overwrite": False,
        "files": model.files,
        "sheets": [
            {
                "id": sheet.id,
                "name": name,
                "source": sheet.source,
                "heading": sheet.heading,
                "kind": sheet.kind,
                "suffixed": suffixed,
                "rows": sum(row.height for row in sheet.rows),
            }
            for sheet, (name, suffixed) in zip(model.sheets, named)
        ],
        "images": images,
        "links": links,
        "warnings": warnings,
    }
    if model.has_readme is not None:
        plan["has_readme"] = model.has_readme
    return plan


def load_plan(path: Path) -> dict:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        raise Refusal(f"cannot read the plan {path}: {err}") from None
    if not isinstance(plan, dict) or plan.get("plan_version") != PLAN_VERSION:
        raise Refusal(f"{path} is not a version-{PLAN_VERSION} plan from this script")
    for key, kind in (("input", str), ("output", str), ("overwrite", bool), ("sheets", list)):
        if not isinstance(plan.get(key), kind):
            raise Refusal(f"the plan's `{key}` is missing or is not a {kind.__name__}")
    if not all(isinstance(sheet, dict) for sheet in plan["sheets"]):
        raise Refusal("the plan's `sheets` holds an entry that is not an object")
    return plan


def matches(plan: dict, model: Model) -> bool:
    """Whether the plan describes the sheets the input still produces."""
    fixed = ("id", "source", "heading", "kind")
    return plan.get("mode") == model.mode and [tuple(s.get(k) for k in fixed) for s in plan["sheets"]] == [
        tuple(getattr(sheet, k) for k in fixed) for sheet in model.sheets
    ]


# --- write ----------------------------------------------------------------------


class Writer:
    """Renders a model into one XlsxWriter workbook under the given sheet names."""

    def __init__(self, path: Path, model: Model, names: list):
        self.book = xlsxwriter.Workbook(str(path), {"in_memory": True})
        self.model = model
        self.names = names
        self.by_id = {sheet.id: name for sheet, name in zip(model.sheets, names)}
        self.formats = {}
        self.late = []  # warnings only writing can discover

    def fmt(self, kind: str = "text", num_format: str = ""):
        key = (kind, num_format)
        if key not in self.formats:
            props = {"text_wrap": True, "valign": "top"}
            props |= {
                "heading": {"bold": True},
                "code": {"font_name": "Courier New"},
                "quote": {"italic": True},
                "warning": {"italic": True, "font_color": "#9C0006"},
                "link": {"font_color": "#0563C1", "underline": 1},
                "heading-link": {"bold": True, "font_color": "#0563C1", "underline": 1},
            }.get(kind, {})
            if num_format:
                props["num_format"] = num_format
            self.formats[key] = self.book.add_format(props)
        return self.formats[key]

    def url(self, link: Link) -> str:
        if link.resolution == "sheet":
            return "internal:'" + self.by_id[link.sheet_id].replace("'", "''") + "'!A1"
        return link.url

    def string(self, ws, row: int, col: int, text: str, fmt) -> None:
        ws.write_string(row, col, text[:MAX_CELL_CHARS], fmt)

    def hyperlink(self, ws, row: int, col: int, link: Link, text: str, fmt) -> None:
        if ws.write_url(row, col, self.url(link), fmt, string=text[:MAX_CELL_CHARS]) != 0:
            self.string(ws, row, col, text, fmt)
            self.late.append(f"{ws.get_name()}!{cell_ref(row, col)}: the hyperlink was refused, so the cell is text")

    def cell(self, ws, row: int, col: int, cell: Cell) -> None:
        if cell.kind == "number":
            ws.write_number(row, col, cell.value, self.fmt("text", cell.num_format))
        elif cell.kind == "date":
            ws.write_datetime(row, col, datetime.datetime.combine(cell.value, datetime.time()), self.fmt("text", cell.num_format))
        elif cell.kind == "boolean":
            ws.write_boolean(row, col, cell.value, self.fmt())
        elif cell.kind == "link":
            self.hyperlink(ws, row, col, cell.link, cell.value, self.fmt("link"))
        elif cell.value:
            self.string(ws, row, col, cell.value, self.fmt())

    def table(self, ws, top: int, row: Row) -> list:
        """Write an Excel Table at `top`; returns each column's display width."""
        last = top + max(1, len(row.cells))
        ws.add_table(top, 0, last, len(row.header) - 1, {"columns": [{"header": h} for h in row.header], "style": "Table Style Medium 2"})
        widths = [len(h) for h in row.header]
        for r, cells in enumerate(row.cells, start=top + 1):
            for c, cell in enumerate(cells):
                self.cell(ws, r, c, cell)
                shown = str(cell.value)
                widths[c] = max(widths[c], max((len(part) for part in shown.split("\n")), default=0))
        return [min(max(w + 2, TABLE_MIN_WIDTH), TABLE_MAX_WIDTH) for w in widths]

    def image(self, ws, top: int, image: ImageRef) -> None:
        scale = min(1.0, PROSE_WIDTH_PX / image.width, (MAX_ROW_HEIGHT_PT / 0.75) / image.height)
        ws.insert_image(top, 0, str(image.file), {"x_scale": scale, "y_scale": scale, "object_position": 1, "description": image.alt or image.path})
        ws.set_row(top, image.height * scale * 0.75)

    def text(self, ws, top: int, row: Row) -> int:
        """Write a prose row; returns how many extra link columns it used."""
        live = [link for link in row.links if link.resolution != "text"]
        if len(live) == 1:
            self.hyperlink(ws, top, 0, live[0], row.text, self.fmt("heading-link" if row.kind == "heading" else "link"))
            return 0
        self.string(ws, top, 0, row.text, self.fmt(row.kind))
        for col, link in enumerate(live if len(live) > 1 else [], start=1):
            self.hyperlink(ws, top, col, link, link.text, self.fmt("link"))
        return len(live) if len(live) > 1 else 0

    def sheet(self, sheet: Sheet, name: str) -> None:
        ws = self.book.add_worksheet(name)
        if sheet.kind == "table":
            for col, width in enumerate(self.table(ws, 0, sheet.rows[0])):
                ws.set_column(col, col, width)
            ws.freeze_panes(1, 0)
            return
        ws.set_column(0, 0, PROSE_WIDTH)
        extra = 0
        for row, top in walk_rows(sheet):
            if row.kind == "table":
                extra = max(extra, len(row.header) - 1)
                self.table(ws, top, row)
            elif row.kind == "image":
                self.image(ws, top, row.image)
            else:
                extra = max(extra, self.text(ws, top, row))
        if extra:
            ws.set_column(1, extra, LINK_WIDTH)

    def close(self) -> None:
        for sheet, name in zip(self.model.sheets, self.names):
            self.sheet(sheet, name)
        self.book.close()


def write_atomically(model: Model, names: list) -> list:
    """Build the workbook at a temporary path, then move it onto the output.

    Before the move the output is untouched, whatever fails. The temporary file
    is removed on every exit path. Returns the warnings only writing found.
    """
    handle, temp = tempfile.mkstemp(prefix="ai-human-xlsx-", suffix=".xlsx")
    os.close(handle)
    try:
        writer = Writer(Path(temp), model, names)
        writer.close()
        shutil.move(temp, model.output)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    mask = os.umask(0)
    os.umask(mask)
    os.chmod(model.output, 0o666 & ~mask)
    return writer.late


# --- the command line -------------------------------------------------------------


def cmd_plan(args) -> None:
    plan = plan_of(build(Path(args.input), Path(args.output) if args.output else None))
    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    if args.save:
        Path(args.save).write_text(text, encoding="utf-8")
    sys.stdout.write(text)


def cmd_write(args) -> None:
    plan = load_plan(Path(args.plan))
    model = build(Path(plan["input"]), Path(plan["output"]))
    if not matches(plan, model):
        raise Refusal(f"the plan no longer matches {model.input}; run `plan` again")
    names = [sheet.get("name") for sheet in plan["sheets"]]
    if problems := name_problems(names):
        raise Refusal("; ".join(problems))
    if model.output.is_dir():
        raise Refusal(f"the output {model.output} is a folder")
    if model.output.exists() and not plan["overwrite"]:
        raise Refusal(f"{model.output} already exists and the plan's `overwrite` is false")
    late = write_atomically(model, names)
    print(f"wrote: {model.output}")
    print(f"sheets: {len(names)}")
    for warning in report(model, names)[2] + late:
        print(f"warning: {warning}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="export_xlsx_cli.py",
        description="Export a markdown file or folder to one .xlsx workbook: `plan` prints the mapping as JSON, `write` writes it.",
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="{plan,write}")
    plan = commands.add_parser("plan", help="print the plan for a .md file or a folder, as JSON")
    plan.add_argument("input", help="a .md file, or a folder of .md files")
    plan.add_argument("--output", help="the workbook path (default: beside the file, or inside the folder)")
    plan.add_argument("--save", metavar="FILE", help="also write the plan to FILE")
    plan.set_defaults(run=cmd_plan)
    write = commands.add_parser("write", help="write the workbook a plan describes")
    write.add_argument("--plan", required=True, metavar="FILE", help="a plan from `plan`, edited or not")
    write.set_defaults(run=cmd_write)
    args = parser.parse_args(argv)
    try:
        args.run(args)
    except Refusal as err:
        print(f"{parser.prog}: error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
