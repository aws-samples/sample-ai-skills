---
title: "Skills"
sidebar_label: "Overview"
sidebar_position: 1
---

# Skills

One page per skill, grouped by domain the way `skills/` in the repository is grouped. Each skill's
page records what it is, how it is invoked, and what it declares; pages documenting a single skill
in depth sit beside that skill's page, and pages covering a whole domain sit at the domain root.

Come here to look something up about a specific skill. For a task spanning more than one skill,
see [How-to](../how-to/); for the reasoning behind a convention, see [Explanation](../explanation/).

## Domains

Each domain page lists the skills it ships.

| Domain | Purpose | # Skills |
|---|---|---|
| [**adr**](./adr/) | a project's architecture decision log | 1 |
| [**agents**](./agents/) | the files a coding agent reads: agent-context files and new skills | 3 |
| [**dev**](./dev/) | recording how a repository is developed, filing issues, carrying a spec or issue to a merge-ready pull or merge request, and the forge's issue, request, and review templates | 4 |
| [**human-docs**](./human-docs/) | prose documents written for people, and their export to PDF, Word, and Excel | 5 |
| [**release**](./release/) | versioning and release notes derived from Conventional Commits, and an optional public publish path | 1 |
| [**research**](./research/) | the spec-driven development loop: a working folder, research, a plan, implementation, and retirement | 5 |
| [**software-docs**](./software-docs/) | a project's documentation tree and the site that builds it | 2 |

Domains are independent and dependency-free: installing one skill from a domain does not require
installing the others, but a skill's own `references/` folder must travel with it.
