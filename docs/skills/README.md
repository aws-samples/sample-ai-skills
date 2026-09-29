---
title: "Skills"
sidebar_label: "Skills"
sidebar_position: 1
---

# Skills

One page per skill, grouped by domain the way `skills/` in the repository is grouped. Each skill's
page records what it is, how it is invoked, and what it declares; pages documenting a single skill
in depth sit beside that skill's page, and pages covering a whole domain sit at the domain root.

Come here to look something up about a specific skill. For a lesson, see
[Tutorial](../tutorial/); for a task spanning more than one skill, see [How-to](../how-to/); for
the reasoning behind a convention, see [Explanation](../explanation/).

## Domains

- [**research**](./research/) — the SDD workflow: `ai-create`, `ai-research`, `ai-plan`,
  `ai-implement`, `ai-archive`
- [**semantic-release**](./semantic-release/) — `ai-release`

Domains are independent and dependency-free: installing one skill from a domain does not require
installing the others, but a skill's own `references/` folder must travel with it.
