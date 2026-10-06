---
title: "ai-create"
sidebar_label: "ai-create"
sidebar_position: 3
---

# `ai-create`

| | |
|---|---|
| Invoke | `/ai-create` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [research](../) |
| Source | `skills/research/ai-create/SKILL.md` |
| Effort | `high` |

## Overview

Create a new working folder with a README.md identity document for a feature or a document.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Denied explicitly rather than left implicit. |
| `Skill` | Step 7 *prints* the next `/ai-…` command for the user to run; it invokes nothing. |
| `NotebookEdit` | The only file written is a `README.md`. |
| `Agent` | No fan-out step. |

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Step 4.7 obtains the date prefix with `date +%F`, which the body insists be *run*, not recalled — a wrong-but-plausible date is invisible on inspection. |
| `Bash(mkdir:*)` | Step 6.1, `mkdir -p <output_root>/<derived-name>/`. |

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
