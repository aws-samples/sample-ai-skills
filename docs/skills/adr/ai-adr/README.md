---
title: "ai-adr"
sidebar_label: "ai-adr"
sidebar_position: 2
---

# `ai-adr`

| | |
|---|---|
| Invoke | `/ai-adr ["<the decision>" \| <verb> <record>]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [adr](../) |
| Source | `skills/adr/ai-adr/SKILL.md` |
| Effort | `high` |

## Overview

Keep a project's architecture decision log — stand it up on first run, then write records and move
them through propose, accept, and decline.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | Step 8 *prints* the literal command for the next transition; it invokes nothing. |
| `NotebookEdit` | The files written are markdown records, the log's `README.md` index, `.adr-dir`, and a block in the root `CLAUDE.md`. |
| `Agent` | No fan-out step. |

**Pre-approval set** — `Bash(date:*), Bash(git config user.name:*), Bash(git config user.email:*), Bash(git rev-parse:*), Bash(find:*), Bash(mkdir:*), Bash(git mv:*), Bash(mv:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Context Loading obtains today's date with `date +%F` rather than recalling it. |
| `Bash(git config user.name:*)` | Context Loading obtains the record's author, who is never the agent. |
| `Bash(git config user.email:*)` | Context Loading offers its local part as a drafted author name when `user.name` is unset. |
| `Bash(git rev-parse:*)` | Steps 1 and 2a write `.adr-dir` at the repository root, and Step 5 uses `git mv` inside a repository and `mv` outside one. The body names no command for either lookup. |
| `Bash(find:*)` | The ENUMERATION rule in `references/adr-format.md` §11, `find "$ADR_DIR" -mindepth 1 -maxdepth 2 -name '*.md'`, which Step 7's index pass runs. |
| `Bash(mkdir:*)` | Step 2a creates `docs/adr`; Steps 5 and 6e create `proposed/` and `retired/` on demand. |
| `Bash(git mv:*)` and `Bash(mv:*)` | Step 5 moves a record to the directory its new status implies — `git mv` inside a repository, so git records a rename, and `mv` outside one. |

The rule Step 2d writes into the log's first record — a person's explicit invocation of `/ai-adr` is
the only route by which a record is written or moved — is **not expressible in either key**. The skill
holds `Write` and `Edit` for the records themselves, and a declaration names capabilities, not the
files they may touch.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
