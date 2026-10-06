"""Carry out a plan; and the manifest that `list` and `uninstall` read.

Each skill is written whole into a sibling temporary directory,
`<target>/.<skill>.partial-<random>`, and renamed into place, so a failure part
way leaves only that directory, which is then removed. That is how "no partial
install" is met without tracking individual files.

The manifest is one dot-file per target skills directory,
`.ai-skills-manifest.json`. A dot-file rather than a directory, so no agent's
skill scanner mistakes it for a skill. Only `list` and `uninstall` consult it;
conflict detection looks only at whether a skill's directory exists.
"""

import json
import os
import secrets
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from . import agents
from .plan import SCOPES, Write, shown

MANIFEST = ".ai-skills-manifest.json"


class ManifestError(Exception):
    pass


@dataclass(frozen=True)
class Outcome:
    write: Write
    #: `written`, `skipped`, `conflict` or `failed`.
    status: str
    detail: str = ""

    def __str__(self) -> str:
        what = f"{self.write.skill.name} for {self.write.agent.label}"
        if self.status == "written":
            return f"wrote {shown(self.write.target)}"
        if self.status == "skipped":
            return f"skipped {what}: {shown(self.write.target)} was left as it is"
        if self.status == "conflict":
            return f"did not write {what}: {shown(self.write.target)} already exists (pass --overwrite to replace it)"
        return f"failed to write {what}: {self.detail}"


def _write_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _install(write: Write, overwrite: bool) -> Outcome:
    parent = write.target.parent
    token = secrets.token_hex(4)
    partial = parent / f".{write.skill.name}.partial-{token}"
    relative = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        for relative, data in write.files.items():
            _write_file(partial / relative, data)
            if relative in write.executable:
                mode = (partial / relative).stat().st_mode
                (partial / relative).chmod(mode | ((mode & 0o444) >> 2))
    except OSError as error:
        shutil.rmtree(partial, ignore_errors=True)
        where = f"{relative}: " if relative else ""
        return Outcome(write, "failed", f"{where}{error}")

    if not os.path.lexists(write.target):
        try:
            os.rename(partial, write.target)
        except OSError as error:
            # Created between the check and the rename.
            shutil.rmtree(partial, ignore_errors=True)
            return Outcome(write, "failed", f"{shown(write.target)}: {error}")
        return Outcome(write, "written")
    if not overwrite:
        shutil.rmtree(partial, ignore_errors=True)
        return Outcome(write, "conflict")
    old = parent / f".{write.skill.name}.old-{token}"
    os.rename(write.target, old)
    try:
        os.rename(partial, write.target)
    except OSError as error:
        os.rename(old, write.target)
        shutil.rmtree(partial, ignore_errors=True)
        return Outcome(write, "failed", str(error))
    if old.is_dir() and not old.is_symlink():
        shutil.rmtree(old)
    else:
        old.unlink()
    return Outcome(write, "written")


def execute(plan, *, version: str, decisions: dict | None = None, overwrite: bool = False) -> list:
    """Write every skill in `plan`, returning one `Outcome` per write.

    `decisions` maps a conflicting target to `overwrite` or `skip`, as the
    conflict screen chose. A conflict with no decision is overwritten only when
    `overwrite` is true, and is otherwise reported and left alone. The existence
    of each target is checked again at write time, not taken from the plan.
    """
    decisions = decisions or {}
    # Read every manifest first: an unreadable one refuses the install before any
    # skill is written, rather than after.
    for directory in {w.target.parent for w in plan.writes}:
        read_manifest(directory)
    outcomes = []
    for write in plan.writes:
        decision = decisions.get(write.target)
        if decision == "skip":
            outcomes.append(Outcome(write, "skipped"))
            continue
        outcomes.append(_install(write, overwrite or decision == "overwrite"))
    written = [o.write for o in outcomes if o.status == "written"]
    for directory in {w.target.parent for w in written}:
        record(directory, [w for w in written if w.target.parent == directory], version)
    return outcomes


# --- the manifest --------------------------------------------------------------


def read_manifest(directory: Path) -> list:
    path = directory / MANIFEST
    if not path.exists():
        return []
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))["entries"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ManifestError(f"{shown(path)} cannot be read ({error}); it was left unchanged") from error
    if not isinstance(entries, list) or not all(
        isinstance(e, dict) and isinstance(e.get("skill"), str) for e in entries
    ):
        raise ManifestError(f"{shown(path)} does not hold a list of skill entries; it was left unchanged")
    return entries


def write_manifest(directory: Path, entries: list) -> None:
    path = directory / MANIFEST
    if not entries:
        path.unlink(missing_ok=True)
        return
    temporary = directory / f"{MANIFEST}.{secrets.token_hex(4)}"
    temporary.write_text(json.dumps({"entries": entries}, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def record(directory: Path, writes: list, version: str) -> None:
    names = {w.skill.name for w in writes}
    entries = [e for e in read_manifest(directory) if e.get("skill") not in names]
    now = datetime.now(UTC).isoformat(timespec="seconds")
    entries += [
        {"skill": w.skill.name, "agent": w.agent.id, "version": version, "installed_at": now}
        for w in sorted(writes, key=lambda w: w.skill.name)
    ]
    write_manifest(directory, entries)


def _is_skill_name(name: str) -> bool:
    """True when `name` is one path component, so `directory / name` is a
    direct child of `directory`.

    A manifest's names are not trusted: at project scope the manifest is a file
    in the repository, and a cloned repository can commit one. `Path("/x").name`
    is `x`, so an absolute path fails the last test. A backslash is refused on
    every platform, so a manifest means the same thing wherever it is read.
    """
    return name not in ("", ".", "..") and "\\" not in name and Path(name).name == name


@dataclass(frozen=True)
class Listing:
    agent: agents.Agent
    scope: str
    directory: Path
    #: `(entry, present)` per recorded skill.
    entries: tuple


def listings(*, home: Path, project: Path, env=os.environ) -> list:
    """Every agent and scope whose skills directory holds a manifest."""
    found = []
    for agent in agents.AGENTS:
        for scope in SCOPES:
            directory = agent.directory(scope, home=home, project=project, env=env)
            entries = read_manifest(directory)
            if entries:
                present = [_is_skill_name(e["skill"]) and (directory / e["skill"]).is_dir() for e in entries]
                found.append(Listing(agent, scope, directory, tuple(zip(entries, present))))
    return found


def uninstall(directory: Path, names: list) -> list:
    """Remove each named skill the manifest in `directory` records.

    Returns `(name, removed, message)` per name. A directory the manifest does
    not name is never removed, even when its name matches a catalog skill. A
    name that is not one path component is refused and its record kept, so
    nothing outside `directory` is removed.
    """
    entries = read_manifest(directory)
    recorded = {e["skill"] for e in entries}
    results = []
    for name in names:
        target = directory / name
        refused = f"refused {name!r}: not a directory name inside {shown(directory)}; nothing was removed"
        if not _is_skill_name(name):
            results.append((name, False, refused))
            continue
        if name not in recorded:
            if os.path.lexists(target):
                results.append((name, False, f"left {shown(target)} in place: this installer did not install it"))
            else:
                results.append((name, False, f"{name} is not installed in {shown(directory)}"))
            continue
        if target.is_dir() and not target.is_symlink():
            # The name passed the string rule; ask the filesystem as well before
            # the one call that cannot be undone.
            if target.resolve().parent != directory.resolve():
                results.append((name, False, refused))
                continue
            shutil.rmtree(target)
            message = f"removed {shown(target)}"
        else:
            message = f"{shown(target)} was already gone; removed its record"
        entries = [e for e in entries if e.get("skill") != name]
        results.append((name, True, message))
    write_manifest(directory, entries)
    return results
