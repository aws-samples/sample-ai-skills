---
title: "ai-create"
sidebar_label: "ai-create"
sidebar_position: 2
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

- **Denied:** `WebFetch`, `WebSearch`, `Skill`, `NotebookEdit`, `Agent`
- **Pre-approved:** `Bash(date:*)`, `Bash(mkdir:*)`

Every entry's reason, and what these declarations do **not** bound, is in
[Tool Grants](../tool-grants.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
