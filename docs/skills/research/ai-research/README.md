---
title: "ai-research"
sidebar_label: "ai-research"
sidebar_position: 6
---

# `ai-research`

| | |
|---|---|
| Invoke | `/ai-research` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [research](../) |
| Source | `skills/research/ai-research/SKILL.md` |
| Effort | `max` |

## Overview

Research a codebase or a topic, producing structured findings; emits SDD phase suggestions only
when asked.

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`framework` only. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. The
framework changes nothing in the research document.
[`ai-scaffold-dev-context`](../../dev/ai-scaffold-dev-context/) records every key at once.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | The description reads "Research a codebase **or a topic**", which plausibly invites web research — but no step in the body fetches anything. This is the single largest untrusted-content surface in the research domain: attacker-controlled fetched text reaching the skill that writes a document two downstream skills treat as authoritative. Denied, not merely omitted. |
| `Skill` | No body invokes another skill. |
| `NotebookEdit` | The files written are `research.md` and, on the auto-create path, a folder `README.md`. |

`Agent` is **not** denied — Step 2b spawns four parallel Explore agents when the scope exceeds ten
files. `Write` and `Edit` are **not** denied either. The body says "Research is read-only", and that
claim scopes to *application code* — the skill still writes `research.md`, may create a folder
README, and edits two manifests.

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(git log:*), Bash(git show:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Context Loading resolves the folder with today's date from `date +%F`. |
| `Bash(mkdir:*)` | Context Loading's auto-create path. |
| `Bash(git log:*)`, `Bash(git show:*)` | Step 2's "Check git history for recent changes that provide context on design decisions" — read-only history, no mutation. |

`Bash(graphify:*)` is **deliberately absent**, and this is a decision rather than an oversight. Step
1b's `graphify query` is optional, the body degrades gracefully without it, and its output is content
the skill then reads *as findings* — so it is an untrusted-input surface, not merely a convenience.
Pre-approving it would remove the one prompt a consumer gets before an external tool runs across
their whole codebase. Stated cost: one permission prompt per run for consumers who use `graphify`. A
reviewer who finds the absence surprising should read this paragraph rather than add the entry.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
