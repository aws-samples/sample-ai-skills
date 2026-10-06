"""Cursor. Reads `metadata` and `disable-model-invocation` beside the required
fields, and also reads Claude Code's and Codex's skills directories.

Source: https://cursor.com/docs/context/skills
"""

from . import Adapted, Agent, adapt_with, home_dir

LABEL = "Cursor"
KEEP = frozenset({"metadata", "disable-model-invocation"})


def adapt(skill, names=()) -> Adapted:
    return adapt_with(skill, agent_label=LABEL, keep=KEEP)


AGENT = Agent(
    id="cursor",
    label=LABEL,
    source="https://cursor.com/docs/context/skills",
    user_dir=home_dir(".cursor", "skills"),
    project_dir=".cursor/skills",
    also_reads=("claude-code", "codex"),
    adapt=adapt,
)
