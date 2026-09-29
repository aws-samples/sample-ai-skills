---
title: "ai-archive"
sidebar_label: "ai-archive"
sidebar_position: 6
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

- **Denied:** `WebFetch`, `WebSearch`, `Skill`, `NotebookEdit`, `Agent`
- **Pre-approved:** `Bash(date:*)`, `Bash(mkdir:*)`, `Bash(git rev-parse:*)`, `Bash(git ls-files:*)`, `Bash(git mv:*)`, `Bash(mv:*)`

Every entry's reason, and what these declarations do **not** bound, is in
[Tool Grants](../tool-grants.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
