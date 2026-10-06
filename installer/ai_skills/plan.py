"""A selection turned into the exact writes an install would make.

The one place that decides what gets written. The TUI and the flags only collect
the selection; both render the plan this module builds and hand it to
`install.execute`. Building a plan reads the catalog and checks whether each
target exists, and writes nothing.
"""

import os
import stat
import subprocess  # nosec B404 # runs git with an argument list, never a shell
from dataclasses import dataclass
from pathlib import Path

from . import agents
from .agents import Notice

SCOPES = ("user", "project")


@dataclass(frozen=True)
class Write:
    agent: agents.Agent
    skill: object
    #: `<agent skills directory>/<skill>`.
    target: Path
    #: Relative POSIX path to the exact bytes written there.
    files: dict
    #: The relative paths written with the execute bit, as in the source.
    executable: frozenset
    #: Whether `target` already exists, as of planning.
    exists: bool


@dataclass(frozen=True)
class Plan:
    scope: str
    project: Path
    writes: tuple
    notices: tuple

    @property
    def conflicts(self) -> tuple:
        return tuple(write for write in self.writes if write.exists)

    def directories(self) -> dict:
        """Each target skills directory, in order, to its agent and writes."""
        grouped = {}
        for write in self.writes:
            grouped.setdefault(write.target.parent, (write.agent, []))[1].append(write)
        return grouped


def shown(path: Path) -> str:
    """`path` as displayed, with the home directory written as `~`."""
    try:
        return str(Path("~") / path.relative_to(Path.home()))
    except ValueError:
        return str(path)


def project_dir(cwd: Path) -> Path:
    """The root of the git repository containing `cwd`, else `cwd` itself."""
    try:
        out = subprocess.run(  # nosec B603 B607 # argument list; git found on PATH
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return cwd
    return Path(out.stdout.strip()) if out.returncode == 0 else cwd


def _is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def overlap_notices(selected: list, scope: str, *, home: Path, project: Path, env) -> list:
    """One notice per selected agent that also reads another selected agent's
    directory, naming both agents and both directories."""
    ids = {agent.id for agent in selected}
    notices = []
    for agent in selected:
        for other_id in agent.also_reads:
            if other_id not in ids:
                continue
            other = agents.get(other_id)
            mine = agent.directory(scope, home=home, project=project, env=env)
            theirs = other.directory(scope, home=home, project=project, env=env)
            notices.append(
                Notice(
                    "overlap",
                    f"{agent.label} will find two copies of each skill: it reads {shown(mine)} and also"
                    f" {shown(theirs)}, which is being written for {other.label}",
                )
            )
    return notices


def build(catalog, agent_ids, skill_names, scope: str, *, cwd: Path, home: Path, env=os.environ) -> Plan:
    """The plan for installing `skill_names` for `agent_ids` at `scope`.

    Raises KeyError naming the first unknown agent or skill, and ValueError for
    an unknown scope, before anything is examined.
    """
    if scope not in SCOPES:
        raise ValueError(f"unknown scope {scope!r}; expected one of {', '.join(SCOPES)}")
    selected = [agents.get(agent_id) for agent_id in agent_ids]
    skills = [catalog.get(name) for name in skill_names]
    project = project_dir(cwd) if scope == "project" else cwd
    writes = []
    notices = []
    for agent in selected:
        directory = agent.directory(scope, home=home, project=project, env=env)
        for skill in skills:
            adapted = agent.adapt(skill, catalog.names)
            files = {}
            for relative in skill.files:
                files[relative] = adapted.skill_md if relative == "SKILL.md" else (skill.path / relative).read_bytes()
            clash = set(adapted.extra) & set(files)
            if clash:
                raise ValueError(f"{agent.label} adapter would replace {sorted(clash)} in {skill.name}")
            files.update(adapted.extra)
            executable = frozenset(r for r in skill.files if _is_executable(skill.path / r))
            target = directory / skill.name
            writes.append(Write(agent, skill, target, files, executable, os.path.lexists(target)))
            notices.extend(adapted.notices)
    notices.extend(overlap_notices(selected, scope, home=home, project=project, env=env))
    return Plan(scope=scope, project=project, writes=tuple(writes), notices=tuple(notices))


def tree(paths) -> list:
    """`paths`, relative POSIX paths, drawn as tree lines."""
    nested = {}
    for path in sorted(paths):
        node = nested
        for part in path.split("/"):
            node = node.setdefault(part, {})
    lines = []

    def walk(node, prefix):
        items = sorted(node.items(), key=lambda item: (not item[1], item[0]))
        for index, (name, child) in enumerate(items):
            last = index == len(items) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{name}{'/' if child else ''}")
            walk(child, prefix + ("    " if last else "│   "))

    walk(nested, "")
    return lines


def render(plan: Plan) -> str:
    """The plan as text: every notice, then each target directory with the tree
    of files written under it. The confirmation screen and `--yes` both show
    this. Notices come first so a long tree cannot push them out of view."""
    lines = []
    if plan.notices:
        lines.append("Warnings:")
        lines += [f"  - {notice}" for notice in plan.notices]
        lines.append("")
    for directory, (agent, writes) in plan.directories().items():
        lines.append(f"{shown(directory)}  ({agent.label})")
        lines += tree(f"{w.skill.name}/{relative}" for w in writes for relative in w.files)
        for write in writes:
            if write.exists:
                lines.append(f"  ! {shown(write.target)} already exists")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"
