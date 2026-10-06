---
title: "ai-agent-context"
sidebar_label: "ai-agent-context"
sidebar_position: 2
---

# `ai-agent-context`

| | |
|---|---|
| Invoke | `/ai-agent-context <directory>` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [agents](../) |
| Source | `skills/agents/ai-agent-context/SKILL.md` |
| Effort | `high` |

## Overview

The skill writes two files into one source directory: a short `CLAUDE.md` holding only the facts an
agent would get wrong without, and a `README.md` holding the structured reference. It reads every file
in the directory in full before writing, and every file name, path, and environment variable it writes
must match the code.

Each candidate fact goes through one test: would an agent working in this directory make a mistake or
waste time without knowing it? A yes goes in `CLAUDE.md`. A no that is still useful goes in
`README.md`. No fact appears in both.

## Arguments

| Argument | Effect |
|---|---|
| a directory | The directory to document. The skill does not decide which directories need context files. |

The skill reads Objectives, Constraints, and Key Terms from the project context set — the root
`README.md`, `AGENTS.md`, and `CLAUDE.md` when present, plus any file `.ai-skills.toml` lists in
`context_files` — and uses them when choosing what goes in `CLAUDE.md`.

## What it writes

| File | Shape |
|---|---|
| `CLAUDE.md` | An H1 naming the directory path from the project root, one or two sentences on what lives there, 3 to 8 bullets of mistake-preventing facts (never more than 10 lines), and a closing line naming what `README.md` covers. |
| `README.md` | A description, a contents table, and only those of these sections that have content: a section specific to the directory, Known Quirks, Environment Variables, Integration Points, Related. |

The facts the skill looks for are: which service or SDK the code wraps, the permissions it needs, the
environment variables it reads, input validation that produces unclear errors, consistency and caching
behavior, how identity flows through the code, rules that are easy to break, and project conventions
that apply to the directory.

The skill does not write docstrings or documentation site pages.

In a repository that keeps agent context in `AGENTS.md` behind `CLAUDE.md` pointers, the `CLAUDE.md`
this skill writes is a file with content, which only Claude Code reads.
[`ai-scaffold-agents-md`](../ai-scaffold-agents-md/) finds it on its next run and
asks before moving the content into `AGENTS.md`.

## Output

The skill ends by checking both files against a validation list: `CLAUDE.md` length, that every named
file, import path, and environment variable exists in the code, that `README.md` has no empty section,
and that no content is duplicated between the two files. It commits nothing.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Every input is a file in the target directory or the project context set. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | The only files it writes are `CLAUDE.md` and `README.md`. |
| `Agent` | No step fans out. The skill reads the directory itself, because every fact it writes must be checked against the code. |

**Pre-approval set** — none. The skill runs no shell command that needs a prompt removed.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
