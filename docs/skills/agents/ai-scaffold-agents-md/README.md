---
title: "ai-scaffold-agents-md"
sidebar_label: "ai-scaffold-agents-md"
sidebar_position: 4
---

# `ai-scaffold-agents-md`

| | |
|---|---|
| Invoke | `/ai-scaffold-agents-md [root] [--dry-run] [--headless]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [agents](../) |
| Source | `skills/agents/ai-scaffold-agents-md/SKILL.md` |
| Effort | `medium` |

## Overview

Codex, Cursor, Copilot, and Gemini CLI read agent context from `AGENTS.md`; Claude Code reads it from
`CLAUDE.md`. When both files hold content they drift apart, and each agent works from different rules.
This skill makes `AGENTS.md` the only file holding content. Beside each one it writes a `CLAUDE.md`
**pointer** whose only loaded content is `@AGENTS.md`, Claude Code's import syntax, so Claude loads
exactly the text every other agent reads.

A `CLAUDE.md` counts as a pointer when, with HTML comments removed, its whole content is `@AGENTS.md`.
Claude Code strips HTML comments before loading the file, so the explanatory comment at the top of
each pointer costs nothing in context. Every pointer the skill writes is byte-identical, and a second
run on a finished tree changes nothing.

The skill does not use a symlink from `CLAUDE.md` to `AGENTS.md`. On a Windows checkout without
symlink support the link becomes a text file holding the target path, and some tools read the link
rather than its target.

## Arguments

| Argument | Effect |
|---|---|
| a directory | The root to work on. Default: the repository root, or the working directory outside a repository. |
| `--dry-run` | Print the plan and stop. Nothing is written. |
| `--headless` | Ask nothing. Take the recommended option of every question and mark each such answer as inferred in the report. |

## What it does in each directory

The skill lists every `AGENTS.md` and `CLAUDE.md` that git tracks or would track, skipping ignored
files, anything under `.claude/`, and `CLAUDE.local.md`. It then handles each directory by what it
finds:

| Found | Action |
|---|---|
| `AGENTS.md` only | Writes the pointer. |
| `AGENTS.md` and a pointer | Nothing. |
| `CLAUDE.md` with content, no `AGENTS.md` | Asks, then copies the content unchanged into `AGENTS.md`, confirms the bytes match with `cmp`, and replaces `CLAUDE.md` with the pointer. |
| `AGENTS.md` holding only `@CLAUDE.md`, and a `CLAUDE.md` with content | The same move. The content replaces the inverted import, which only Claude Code can follow. |
| Both files with content | Asks. The recommended answer leaves both in place, because deciding which of two contradicting rules wins is the owner's decision. |
| Neither file, at the root | Asks. The recommended answer creates a root `AGENTS.md` holding only the convention block, and its pointer. |
| A symlink, a directory, a non-UTF-8 file, a case variant such as `claude.md`, or a pointer with no `AGENTS.md` | Reports it and changes nothing. |

Moved content is never edited. The report lists every `@path` import in moved content, because only
Claude Code follows those imports and every other agent sees a literal line. It also lists every
mention of `CLAUDE.md` by name, which after the move describes a pointer.

## The convention block

After confirmation, the skill adds a short section to the root `AGENTS.md` stating the rule: put agent
context in the nearest `AGENTS.md`, and never write content into a `CLAUDE.md` pointer. The section is
fenced by `<!-- ai-skills:agents-md -->` and `<!-- /ai-skills:agents-md -->`, so a later run replaces
it instead of adding a second copy.

## Output

Every run ends with one line per file (`created`, `moved`, `kept`, `left`, `warn`), the number of
directories examined, the files left for a person with the decision each one needs, and every answer
taken as a default. The skill commits nothing, so review `git status` and `git diff` before
committing.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Every input is a file in the working tree. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | The only files it writes are `AGENTS.md` and `CLAUDE.md`. |
| `Agent` | No step fans out. The tree walk is one `git ls-files` call. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(git ls-files:*), Bash(test:*), Bash(cmp:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(git ls-files:*)` | Steps 1 and 6, listing every `AGENTS.md` and `CLAUDE.md` that git tracks or would track. |
| `Bash(test:*)` | Step 2, checking with `test -L` and `test -f` that a `CLAUDE.md` is a regular file before reading it. |
| `Bash(cmp:*)` | Step 4, confirming a moved `AGENTS.md` matches its `CLAUDE.md` byte for byte before the pointer overwrites `CLAUDE.md`. |

All four commands only read. None of them changes a file.

**`cp` is deliberately not pre-approved**, although Step 4 uses it to move content. `cp` overwrites
its destination, and in the inverted case that destination is an existing `AGENTS.md`. Leaving it
unapproved means each copy prompts, so a person sees every file the skill is about to replace.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
