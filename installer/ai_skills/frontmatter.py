"""`SKILL.md` frontmatter, filtered by line and never re-serialized.

A YAML library would re-quote values and reorder keys, so every adapted
`SKILL.md` would differ from its source in ways that are not changes. Instead the
file is split at its first two `---` lines, and whole top-level entries are kept
or dropped with their bytes untouched. An entry is a line beginning `key:` at
column 0 plus every line after it up to the next such line, so a value that
spans several lines is kept or dropped whole.

The result is then parsed, and refused if it does not parse or if `name` is not
the skill's directory name. That is the backstop for a frontmatter shape this
line-level rule does not anticipate: it fails at `make installer-tests`, which
runs every catalog skill through every adapter, rather than at a user's install.
"""

import re
from dataclasses import dataclass, replace

import yaml

_DELIMITER = b"---"
_KEY = re.compile(rb"^([A-Za-z0-9_-]+):")


class FrontmatterError(Exception):
    pass


@dataclass(frozen=True)
class Document:
    opening: bytes
    #: The lines between the delimiters, each with its line ending.
    lines: tuple
    closing: bytes
    body: bytes

    @property
    def block(self) -> bytes:
        return b"".join(self.lines)

    def render(self) -> bytes:
        return self.opening + self.block + self.closing + self.body


def split(source: bytes) -> Document:
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != _DELIMITER:
        raise FrontmatterError("does not begin with a --- line")
    for index in range(1, len(lines)):
        if lines[index].rstrip(b"\r\n") == _DELIMITER:
            return Document(
                opening=lines[0],
                lines=tuple(lines[1:index]),
                closing=lines[index],
                body=b"".join(lines[index + 1 :]),
            )
    raise FrontmatterError("has no closing --- line")


def entries(document: Document) -> list:
    """`(key, lines)` per top-level entry, in order. Lines before the first key
    have the key None."""
    grouped = []
    for line in document.lines:
        match = _KEY.match(line)
        if match or not grouped:
            grouped.append((match.group(1).decode("ascii") if match else None, [line]))
        else:
            grouped[-1][1].append(line)
    return grouped


def keep(document: Document, keys) -> Document:
    """`document` with only the entries whose key is in `keys`. Lines that
    belong to no key are kept."""
    kept = [line for key, lines in entries(document) if key is None or key in keys for line in lines]
    return replace(document, lines=tuple(kept))


def append(source: bytes, section: str) -> bytes:
    """`source` with `section` added after a blank line. The existing bytes are
    unchanged apart from a final newline supplied if one is missing."""
    if not source.endswith(b"\n"):
        source += b"\n"
    return source + b"\n" + section.encode("utf-8")


def validate(source: bytes, name: str) -> None:
    """Refuse `source` unless its frontmatter parses and `name` matches."""
    try:
        fields = yaml.safe_load(split(source).block.decode("utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError) as error:
        raise FrontmatterError(f"frontmatter does not parse: {error}") from error
    if not isinstance(fields, dict):
        raise FrontmatterError("frontmatter is not a mapping")
    if fields.get("name") != name:
        raise FrontmatterError(f"frontmatter `name` is {fields.get('name')!r}, not {name!r}")
