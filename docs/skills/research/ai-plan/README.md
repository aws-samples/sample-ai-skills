---
title: "ai-plan"
sidebar_label: "ai-plan"
sidebar_position: 5
---

# `ai-plan`

| | |
|---|---|
| Invoke | `/ai-plan` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [research](../) |
| Source | `skills/research/ai-plan/SKILL.md` |
| Effort | `xhigh` |

## Overview

Create a comprehensive implementation plan for a feature, with phases, code samples, and testing
strategy.

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`framework` only. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. The
framework changes nothing in the plan.
[`ai-scaffold-dev-context`](../../dev/ai-scaffold-dev-context/) records every key at once.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | The closing section prints the next command; it invokes nothing. |
| `NotebookEdit` | The files written are `plan.md` and, on the auto-create path, a folder `README.md`. |
| `Agent` | `ai-plan` has **no fan-out step**. This is the one row that differs from [`ai-research`](../ai-research/) and [`ai-implement`](../ai-implement/), which both fan out and leave `Agent` undenied. |

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(find:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Context Loading's folder resolution. |
| `Bash(mkdir:*)` | Context Loading's auto-create path. |
| `Bash(find:*)` | The ADR-log enumeration the body spells out literally: `find <log> -mindepth 1 -maxdepth 2 -name '*.md'`. |

`Bash(graphify:*)` is absent for the reason given under [`ai-research`](../ai-research/#tool-grants).

One limit worth naming here, because it is the clearest single illustration of the
[write-target gap](../../../explanation/tool-grant-bounds.md#what-these-declarations-do-not-bound):
the body's strongest constraint is **"Read a status; never write one, and never write a record"**, and
that is **not expressible in either key**. `ai-plan` legitimately holds `Write` and `Edit` for
`plan.md`, so no declaration can stop it writing into an ADR log. That constraint is prose and can
only be prose.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
