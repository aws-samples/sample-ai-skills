"""Kiro. Reads the Agent Skills specification's fields and no way to disable
model invocation, so explicit-only skills say so in the body.

Source: https://kiro.dev/docs/skills/
"""

from . import Adapted, Agent, adapt_with, home_dir

LABEL = "Kiro"
KEEP = frozenset({"license", "compatibility", "metadata"})


def adapt(skill, names=()) -> Adapted:
    return adapt_with(skill, agent_label=LABEL, keep=KEEP, explicit_only_in_body=True)


AGENT = Agent(
    id="kiro",
    label=LABEL,
    source="https://kiro.dev/docs/skills/",
    user_dir=home_dir(".kiro", "skills"),
    project_dir=".kiro/skills",
    also_reads=(),
    adapt=adapt,
)
