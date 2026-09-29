---
title: "ai-research"
sidebar_label: "ai-research"
sidebar_position: 3
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

## Tool grants

- **Denied:** `WebFetch`, `WebSearch`, `Skill`, `NotebookEdit`
- **Pre-approved:** `Bash(date:*)`, `Bash(mkdir:*)`, `Bash(git log:*)`, `Bash(git show:*)`

Every entry's reason, and what these declarations do **not** bound, is in
[Tool Grants](../tool-grants.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
