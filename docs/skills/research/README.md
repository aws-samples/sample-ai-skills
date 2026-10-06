---
title: "research"
sidebar_label: "research"
sidebar_position: 7
---

# `research`

The SDD workflow: five skills that carry a piece of work from a new folder through research, a
plan, implementation, and retirement. Each is invoked only by its slash command.

| Skill | What it does |
|---|---|
| [`ai-archive`](./ai-archive/) | retires a finished folder into the working root's `.archive/` |
| [`ai-create`](./ai-create/) | creates a working folder with a README.md identity document |
| [`ai-implement`](./ai-implement/) | executes a plan, building the code it specifies |
| [`ai-plan`](./ai-plan/) | writes an implementation plan with phases, samples, and test strategy |
| [`ai-research`](./ai-research/) | researches a codebase or topic, producing structured findings |

The canonical shared references for this domain live at `skills/research/.ai-research-reference/`
(`voice.md`, `manifest-update.md`, `graphify-integration.md`, `adr-consumer.md`). Each skill
carries its own per-skill copy of the references it cites, in that skill's `references/` folder.
[Skill Naming](../../explanation/skill-naming.md) explains why the source directory's name starts
with a dot.
