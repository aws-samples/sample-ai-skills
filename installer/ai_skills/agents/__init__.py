"""The supported agents, and what their adapters share.

Each module here declares one agent: where it reads skills at user and project
scope, which other agents' directories it also reads, and `adapt()`, which turns
a catalog skill's `SKILL.md` into the one that agent should receive. Adding an
agent is one module plus a line in `AGENTS` below; the planner and the TUI read
only this registry.

Agents differ only in which frontmatter fields they keep and which of the
helpers below they call, so most of an adapter is a field list.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from .. import frontmatter

#: Always kept: every agent requires both.
REQUIRED = frozenset({"name", "description"})

#: The fields a skill uses to bound its tools. Claude Code enforces both; every
#: other agent is treated as enforcing neither.
TOOL_FIELDS = ("disallowed-tools", "allowed-tools")


@dataclass(frozen=True)
class Notice:
    """A warning for the confirmation screen and non-interactive output."""

    #: `restriction`, `explicit-only` or `overlap`.
    kind: str
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True)
class Adapted:
    skill_md: bytes
    #: Files the adapter adds beside `SKILL.md`, relative path to content.
    extra: dict = field(default_factory=dict)
    notices: tuple = ()


@dataclass(frozen=True)
class Agent:
    id: str
    label: str
    #: The vendor page the directories and fields were taken from.
    source: str
    user_dir: Callable
    project_dir: str
    #: Ids of the agents whose directories this agent also reads.
    also_reads: tuple
    adapt: Callable

    def directory(self, scope: str, *, home: Path, project: Path, env=os.environ) -> Path:
        if scope == "user":
            return self.user_dir(home, env)
        if scope == "project":
            return project / self.project_dir
        raise ValueError(f"unknown scope {scope!r}")


def home_dir(*parts: str) -> Callable:
    """A `user_dir` resolving to `~/<parts>`."""
    return lambda home, env: home.joinpath(*parts)


# --- the shared adapter steps ------------------------------------------------


def tool_values(value) -> list:
    """A tool declaration as a list of entries.

    The skills write one comma-separated string; a YAML list is accepted too. A
    comma inside parentheses belongs to its entry, not to the separator.
    """
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    entries, depth, current = [], 0, ""
    for char in str(value or ""):
        depth += {"(": 1, ")": -1}.get(char, 0)
        if char == "," and depth == 0:
            entries.append(current.strip())
            current = ""
        else:
            current += char
    entries.append(current.strip())
    return [entry for entry in entries if entry]


def restrictions_section(skill, agent_label: str) -> str | None:
    """The "Tool restrictions" section for an agent that enforces neither tool
    field, or None when the skill declares neither.

    `disallowed-tools` becomes a list of tools not to use. `allowed-tools` is a
    PRE-APPROVAL set in Claude Code, not a limit — docs/explanation/
    tool-grant-bounds.md — so it is listed as the commands the skill runs, and
    said to restrict nothing. Stating it as "use only these" would invent a
    restriction the skill never declared.
    """
    denied = tool_values(skill.fields.get("disallowed-tools"))
    allowed = tool_values(skill.fields.get("allowed-tools"))
    if not denied and not allowed:
        return None
    lines = [
        "## Tool restrictions",
        "",
        f"This skill was written for an agent that enforces the tool declarations in its frontmatter."
        f" {agent_label} does not enforce them, so they are stated here, and you must follow them"
        " yourself. An entry `Bash(<command>:*)` means any shell command that starts with `<command>`.",
    ]
    if denied:
        lines += ["", "Do not use these tools:", ""] + [f"- `{entry}`" for entry in denied]
    if allowed:
        lines += [
            "",
            "This skill's steps run these commands. The list does not limit which other tools you may use:",
            "",
        ] + [f"- `{entry}`" for entry in allowed]
    return "\n".join(lines) + "\n"


def restriction_notice(skill, agent_label: str) -> Notice:
    return Notice(
        "restriction",
        f"{skill.name} for {agent_label}: its tool restrictions are stated in SKILL.md, not enforced",
    )


def explicit_only(skill) -> bool:
    return skill.fields.get("disable-model-invocation") is True


def explicit_only_section() -> str:
    return (
        "## Invocation\n"
        "\n"
        "Run this skill only when the user invokes it by name. Do not start it on your own because a"
        " request looks related to what it does.\n"
    )


def explicit_only_notice(skill, agent_label: str) -> Notice:
    return Notice(
        "explicit-only",
        f"{skill.name} for {agent_label}: running only when invoked is stated in SKILL.md, not enforced",
    )


def rewrite_invocations(text: str, names, replacement: Callable) -> str:
    """Replace `/<name>` with `replacement(name)` for each catalog name.

    Only where the `/` does not follow a path character (a letter, digit, `.`,
    `_`, `-` or `/`), and only where the name ends there. So `` `/ai-plan` `` and
    "the /ai-plan slash command" are rewritten, while `.claude/skills/ai-plan/`
    and `/ai-plan-extra` are left alone.
    """
    if not names:
        return text
    alternatives = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    pattern = re.compile(rf"(?<![A-Za-z0-9._/-])/({alternatives})(?![A-Za-z0-9_-])")
    return pattern.sub(lambda match: replacement(match.group(1)), text)


def adapt_with(
    skill,
    *,
    agent_label: str,
    keep: frozenset,
    restrictions: bool = True,
    explicit_only_in_body: bool = False,
    rewrite: Callable | None = None,
    names=(),
) -> Adapted:
    """The adapter every agent but Claude Code is built from.

    Keeps `name`, `description` and `keep`; rewrites invocations when `rewrite`
    is given; then appends the explicit-only statement and, last, the "Tool
    restrictions" section, which the spec requires the file to end with.
    """
    document = frontmatter.keep(frontmatter.split(skill.source), REQUIRED | keep)
    output = document.render()
    if rewrite is not None:
        output = rewrite_invocations(output.decode("utf-8"), names, rewrite).encode("utf-8")
    notices = []
    if explicit_only_in_body and explicit_only(skill):
        output = frontmatter.append(output, explicit_only_section())
        notices.append(explicit_only_notice(skill, agent_label))
    section = restrictions_section(skill, agent_label) if restrictions else None
    if section is not None:
        output = frontmatter.append(output, section)
        notices.append(restriction_notice(skill, agent_label))
    frontmatter.validate(output, skill.name)
    return Adapted(skill_md=output, notices=tuple(notices))


def yaml_dump(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


from . import claude_code, codex, cursor, kiro, opencode, pi  # noqa: E402

#: Every supported agent, in the order the agent screen lists them.
AGENTS = (
    claude_code.AGENT,
    kiro.AGENT,
    codex.AGENT,
    opencode.AGENT,
    pi.AGENT,
    cursor.AGENT,
)


def get(agent_id: str) -> Agent:
    for agent in AGENTS:
        if agent.id == agent_id:
            return agent
    raise KeyError(agent_id)
