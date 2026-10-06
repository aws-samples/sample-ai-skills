---
title: "ai-archive"
sidebar_label: "ai-archive"
sidebar_position: 2
---

# `ai-archive`

| | |
|---|---|
| Invoke | `/ai-archive` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [research](../) |
| Source | `skills/research/ai-archive/SKILL.md` |
| Effort | `medium` |

## Overview

Retire one finished work folder by moving it into the working root's .archive/ directory and
transferring its manifest row.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | No body invokes another skill; there is no `/ai-unarchive`, and Step 10 prints the restore command instead. |
| `NotebookEdit` | The files written are two manifest `README.md` files. |
| `Agent` | No fan-out step — one folder per invocation, by design. |

`Write` and `Edit` are **not** denied: Step 7 deletes a manifest row with `Edit`, and Step 8 creates
or updates `<output_root>/.archive/README.md` with `Write`. This skill performs the research domain's
only destructive, hard-to-reverse filesystem mutation, which is exactly why its declarations were
derived from its body rather than from any summary claiming it does not need write.

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git mv:*), Bash(mv:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Steps 7 and 8 both take today's date from `date +%F`. |
| `Bash(mkdir:*)` | Step 5, `mkdir -p <output_root>/.archive/` — run before the move, because `git mv` fails when the destination's parent is absent. |
| `Bash(git rev-parse:*)` | Step 6.1, `git rev-parse --is-inside-work-tree`. |
| `Bash(git ls-files:*)` | Step 6.2, `git ls-files --error-unmatch`. |
| `Bash(git mv:*)` and `Bash(mv:*)` | Step 6's tracking branch — `git mv` on a tracked folder, plain `mv` otherwise. |

**Both move commands are pre-approved and neither is denied**, which is load-bearing rather than
convenient. The body's own analysis is that using the wrong one destroys the work: plain `mv` on a
*tracked* folder makes git record a deletion, so the archived content is absent from every future
checkout. Denying or failing to pre-approve either command would push the run toward the destructive
fallback Step 6 explicitly forbids.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
