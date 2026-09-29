---
title: "semantic-release"
sidebar_label: "semantic-release"
sidebar_position: 2
---

# `semantic-release`

One skill that configures how a repository releases — internally, and on request publicly. It
activates from its slash command or from a request matching its description.

| Skill | What it does |
|---|---|
| [`ai-release`](./ai-release/) | configures the internal release path — version derivation, git-cliff config, release and forge-release scripts, CI jobs, bootstrap tag — and, only when publishing is what was asked for, a promote path that publishes one tag's filtered tree to a public target |

The domain's public-publish capability is carried by that one skill rather than a second one. The
retired predecessor packaged a single repository's publish policy as nine refusal gates and installed
nothing; the promote half carries **three** refusals and leaves every other check to the repository
that installs it, reachable from a written forwarding address. The two halves are never installed as a
side effect of one another.

Shipping the capability is not the same as using it. **This repository has no public publish path**:
no promote configuration, no promote script at its root, no promote job, and no push credential.

## Domain pages

- [Commit Conventions](commit-conventions.md) — the Conventional Commits format both the release
  notes and the version bump are derived from, which subjects bump what, and where the convention
  is enforced.
- [Tool Grants](tool-grants.md) — the denial and pre-approval sets the skill declares, the reason
  for every entry, and what those declarations do not bound.
