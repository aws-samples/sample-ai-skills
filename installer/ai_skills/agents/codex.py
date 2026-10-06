"""Codex. Reads the Agent Skills specification's fields; turns implicit
invocation off through `agents/openai.yaml` rather than a frontmatter field; and
is invoked as `$<name>`, not `/<name>`.

Source: https://learn.chatgpt.com/docs/build-skills
"""

from . import Adapted, Agent, adapt_with, explicit_only, home_dir, yaml_dump

LABEL = "Codex"
KEEP = frozenset({"license", "compatibility", "metadata"})

#: Where Codex reads a skill's invocation policy, relative to the skill.
POLICY_FILE = "agents/openai.yaml"


def adapt(skill, names=()) -> Adapted:
    adapted = adapt_with(skill, agent_label=LABEL, keep=KEEP, rewrite=lambda name: f"${name}", names=names)
    if not explicit_only(skill):
        return adapted
    policy = (
        f"# Written by ai-skills: {skill.name} declares disable-model-invocation, so Codex\n"
        "# runs it only when the user invokes it.\n"
        + yaml_dump({"policy": {"allow_implicit_invocation": False}})
    )
    return Adapted(skill_md=adapted.skill_md, extra={POLICY_FILE: policy.encode("utf-8")}, notices=adapted.notices)


AGENT = Agent(
    id="codex",
    label=LABEL,
    source="https://learn.chatgpt.com/docs/build-skills",
    user_dir=home_dir(".agents", "skills"),
    project_dir=".agents/skills",
    also_reads=(),
    adapt=adapt,
)
