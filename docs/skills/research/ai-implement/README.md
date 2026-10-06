---
title: "ai-implement"
sidebar_label: "ai-implement"
sidebar_position: 4
---

# `ai-implement`

| | |
|---|---|
| Invoke | `/ai-implement` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [research](../) |
| Source | `skills/research/ai-implement/SKILL.md` |
| Effort | `xhigh` |

## Overview

Execute an implementation plan for a feature by building all code specified in it.

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`framework` and `verify`. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. A
recorded `verify` is the first test command its final verification runs.
[`ai-scaffold-dev-context`](../../dev/ai-scaffold-dev-context/) records every key at once.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | Where the body wants a plan, it tells the *user* to run `/ai-plan`; it invokes nothing. It also states that no ADR-authoring skill exists here. |
| `NotebookEdit` | No step names a notebook. |

`Agent` is **not** denied — Step 2b dispatches one agent per independent phase.

**`Bash` is not denied and is not scoped.** Step 3a installs "any packages the plan requires" and
Step 4.2 detects and runs an unknown project's test command from `package.json`, `pyproject.toml`,
`Cargo.toml`, or a `Makefile`. Any command allowlist here would be either a lie or a guess that
breaks the skill in the first repository using a different runner.

**Pre-approval set — none. This skill declares no `allowed-tools` key at all.**

That is the most consequential single line in these declarations, and it is a deliberate empty set
rather than an omission. No honest command scope can be written for a skill that runs an unknown
project's test runner, and a bare `Bash` entry here would auto-approve *every* command for the
invoking turn — before the consumer's permission callback is consulted, injected commands included —
on the skill most able to do damage. The correct pre-approval set is therefore the empty one: no key,
and the consumer's own permission prompts left intact.

**Said plainly: the denial set buys nearly nothing for this skill.** `ai-implement` is the skill
excessive agency is actually about, and it is the skill a tool-restriction mechanism helps least. Its
real bound is the write-path constraint in its body plus the harness's own permission prompt — not
anything in this section.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

- [Implementation Write Bounds](implementation-write-bounds.md)
