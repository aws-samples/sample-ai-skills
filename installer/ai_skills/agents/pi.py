"""pi. Reads the specification's fields plus `allowed-tools` and
`disable-model-invocation`, is invoked as `/skill:<name>`, and also reads
Codex's skills directory. Its user directory moves with `PI_CODING_AGENT_DIR`.

pi documents `allowed-tools` only as experimental, so it is kept and the "Tool
restrictions" section is added as well.

Source: https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/skills.md
and .../docs/configuration.md
"""

from pathlib import Path

from . import Adapted, Agent, adapt_with

LABEL = "pi"
KEEP = frozenset({"license", "compatibility", "metadata", "allowed-tools", "disable-model-invocation"})


def user_dir(home, env):
    override = env.get("PI_CODING_AGENT_DIR")
    return (Path(override) if override else home / ".pi" / "agent") / "skills"


def adapt(skill, names=()) -> Adapted:
    return adapt_with(skill, agent_label=LABEL, keep=KEEP, rewrite=lambda name: f"/skill:{name}", names=names)


AGENT = Agent(
    id="pi",
    label=LABEL,
    source="https://raw.githubusercontent.com/earendil-works/pi/main/packages/coding-agent/docs/skills.md",
    user_dir=user_dir,
    project_dir=".pi/skills",
    also_reads=("codex",),
    adapt=adapt,
)
