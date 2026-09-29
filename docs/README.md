---
title: "Overview"
sidebar_position: 1
slug: /
---

# `ai-skills`

Reusable skills for AI coding agents. They give an agent your project's patterns, constraints, and
conventions, so its output is consistent from one run to the next.

Each skill is a self-contained directory holding a `SKILL.md` and the reference material it needs,
following the [Agent Skills](https://agentskills.io) format, so any coding agent that loads skills
can use them. Skills are grouped by domain: one domain covers a spec-driven development workflow,
taking a feature from research through planning to implementation; another sets up versioning and
release notes derived from Conventional Commits. Domains are independent, so you can install one
skill without the others.

## Install a skill

Copy a skill's directory from the repository's `skills/` tree, including its `references/` folder,
into the skills directory your agent reads, either at the project level or at the user level to make
it available in every project. See your agent's documentation for where that directory is.

## Where to go next

The documentation is organized on two axes. [**Skills**](./skills/) is the product axis — one page
per skill, grouped by domain. The remaining [Diátaxis](https://diataxis.fr) sections hold what no
single skill owns:

- [**Skills**](./skills/) — what each skill is, how it is invoked, what it declares
- [**Tutorial**](./tutorial/) — a guided first success, every choice made for you
- [**How-to**](./how-to/) — you bring the goal, the guide gives the shortest route
- [**Explanation**](./explanation/) — the reasoning behind a convention
