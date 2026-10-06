"""OpenCode. Reads the Agent Skills specification's fields and no way to disable
model invocation. Also reads Claude Code's and Codex's skills directories.

Source: https://opencode.ai/docs/skills
"""

from . import Adapted, Agent, adapt_with, home_dir

LABEL = "OpenCode"
KEEP = frozenset({"license", "compatibility", "metadata"})


def adapt(skill, names=()) -> Adapted:
    return adapt_with(skill, agent_label=LABEL, keep=KEEP, explicit_only_in_body=True)


AGENT = Agent(
    id="opencode",
    label=LABEL,
    source="https://opencode.ai/docs/skills",
    user_dir=home_dir(".config", "opencode", "skills"),
    project_dir=".opencode/skills",
    also_reads=("claude-code", "codex"),
    adapt=adapt,
)
