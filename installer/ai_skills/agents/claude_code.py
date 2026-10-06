"""Claude Code. The skills are written in its frontmatter dialect, so its copy of
`SKILL.md` is the source, byte for byte, and gains no section.

Source: https://code.claude.com/docs/en/skills
"""

from . import Adapted, Agent, home_dir


def adapt(skill, names=()) -> Adapted:
    return Adapted(skill_md=skill.source)


AGENT = Agent(
    id="claude-code",
    label="Claude Code",
    source="https://code.claude.com/docs/en/skills",
    user_dir=home_dir(".claude", "skills"),
    project_dir=".claude/skills",
    also_reads=(),
    adapt=adapt,
)
