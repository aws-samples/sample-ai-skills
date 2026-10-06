"""The catalog: every skill in the skills tree, read at run time.

There is no hand-maintained list. A skill is a directory
`<root>/<domain>/<skill>/` holding a `SKILL.md`, and everything under that
directory, at every depth, is part of it. A domain-level source such as
`skills/research/.ai-research-reference/` holds no `SKILL.md`, so it is never a
skill.

The root is the copy packaged into the wheel when there is one — the case for a
`uvx --from git+…` install — and otherwise the `skills/` of the git repository
this package sits in, which is the case for `uv run ai-skills` from a clone. The
repository root comes from git, asked from this file's own directory, rather
than from counting parent directories.
"""

import subprocess  # nosec B404 # runs git with an argument list, never a shell
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

import yaml

from . import frontmatter


class CatalogError(Exception):
    """The catalog cannot be read. The message names what was searched."""


@dataclass(frozen=True)
class Skill:
    name: str
    domain: str
    description: str
    #: The skill's directory in the catalog root.
    path: Path
    #: Every file under `path`, as sorted POSIX paths relative to it.
    files: tuple
    #: `SKILL.md` exactly as it is in the tree.
    source: bytes
    #: The frontmatter, parsed: what the adapters decide on.
    fields: dict


@dataclass(frozen=True)
class Catalog:
    root: Path
    skills: tuple

    @property
    def names(self) -> tuple:
        return tuple(skill.name for skill in self.skills)

    def get(self, name: str) -> Skill:
        for skill in self.skills:
            if skill.name == name:
                return skill
        raise KeyError(name)

    def by_domain(self) -> dict:
        """Domain to skills, both in sorted order."""
        grouped = {}
        for skill in self.skills:
            grouped.setdefault(skill.domain, []).append(skill)
        return grouped


def packaged_root() -> Path:
    """Where a built wheel carries the catalog. Absent in an editable install."""
    return Path(str(files("ai_skills") / "_skills"))


def repository_root() -> Path | None:
    """`skills/` in the git repository this package sits in, or None."""
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(  # nosec B603 B607 # argument list; git found on PATH
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if out.returncode != 0:
        return None
    return Path(out.stdout.strip()) / "skills"


def default_roots() -> list:
    """The roots to try, in order. A missing git repository is left out."""
    roots = [packaged_root()]
    repository = repository_root()
    if repository is not None:
        roots.append(repository)
    return roots


def _files(directory: Path) -> tuple:
    return tuple(
        sorted(path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file())
    )


def read_skill(directory: Path) -> Skill:
    source = (directory / "SKILL.md").read_bytes()
    shown = directory / "SKILL.md"
    try:
        document = frontmatter.split(source)
        fields = yaml.safe_load(document.block.decode("utf-8"))
    except (frontmatter.FrontmatterError, yaml.YAMLError, UnicodeDecodeError) as error:
        raise CatalogError(f"{shown}: frontmatter cannot be read: {error}") from error
    if not isinstance(fields, dict) or fields.get("name") != directory.name:
        raise CatalogError(f"{shown}: frontmatter `name` is not {directory.name!r}")
    if not isinstance(fields.get("description"), str):
        raise CatalogError(f"{shown}: frontmatter has no `description`")
    return Skill(
        name=directory.name,
        domain=directory.parent.name,
        description=fields["description"],
        path=directory,
        files=_files(directory),
        source=source,
        fields=fields,
    )


def load(roots: list | None = None) -> Catalog:
    """The catalog from the first root that exists.

    Raises `CatalogError` naming every root tried when none exists, and naming
    the root searched when it holds no skill.
    """
    roots = default_roots() if roots is None else roots
    root = next((r for r in roots if r.is_dir()), None)
    if root is None:
        tried = ", ".join(str(r) for r in roots) or "(none)"
        raise CatalogError(f"found no skills directory; tried {tried}")
    skills = tuple(
        read_skill(path.parent)
        for path in sorted(root.glob("*/*/SKILL.md"), key=lambda p: (p.parent.parent.name, p.parent.name))
    )
    if not skills:
        raise CatalogError(f"found no skills: no <domain>/<skill>/SKILL.md under {root}")
    return Catalog(root=root, skills=skills)
