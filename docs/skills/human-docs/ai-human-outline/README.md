---
title: "ai-human-outline"
sidebar_label: "ai-human-outline"
sidebar_position: 4
---

# `ai-human-outline`

| | |
|---|---|
| Invoke | `/ai-human-outline <name>`, or `/ai-human-outline <name> --headless` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [human-docs](../) |
| Source | `skills/human-docs/ai-human-outline/SKILL.md` |
| Effort | `high` |

## Overview

The skill turns a document folder into `outline.md`, the blueprint a drafter writes the document
from. The outline holds a heading hierarchy with two to four guidance bullets under every heading, a
table mapping each objective to the sections that serve it, Validation Notes, and a
Human-in-the-Loop (HITL) Review block. HITL items are the decisions a person answers before
drafting, each with a recommended choice. When no folder matches the name, the skill creates one.
It runs with no other skill installed.

The outline is validated against a **constitution**: the voice rules of its `voice.md`, which are
always present, plus every `Constraints` bullet in the project context. Its principle count is never
zero. When two context files state constraints that one outline cannot satisfy together, the skill
names both files, quotes both constraints, and writes nothing until the user says which applies.

## Where it looks

| Input | Source |
|---|---|
| the working root | `output_path` in `.ai-skills.toml`, or `docs/working`; the skill never writes that file |
| project constraints | the root `README.md`, `AGENTS.md`, and `CLAUDE.md`, then each `context_files` entry |
| objectives | the folder README's `## Requirements`, or, when it states none, objectives drafted from `## Description` and confirmed in the interview |
| audience and scope | the folder README's `## Audience` and `## Scope` |
| research | the folder's `research.md`, when it exists |

A short name binds to a dated folder: `onboarding-guide` finds `2026-09-02-onboarding-guide/`. When
more than one dated folder matches, the skill lists them and asks, and never picks by date. When none
matches, it interviews for a title, description, and audience, and writes the folder's `README.md`
before outlining.

## The interview

The skill asks rather than guesses, in rounds of one to four questions, and every question carries a
recommended option. The user can end the interview in any round. `--headless` asks nothing and takes
every recommended option. Either way, each answer taken by default is marked ` — *(inferred)*` in
`outline.md`. A question guarding a choice that a warning could not undo has **Stop** as its
recommended option, so a headless run or an early end never makes that choice. Those questions are
which of two dated folders to use, and which conflicting constraint applies.

## Output

The skill writes `<folder>/outline.md`, and says so before replacing an existing one. A rerun
regenerates the outline rather than revising it. It then checks `In progress` in the folder README's
Status, never `Complete`, and updates that folder's row in the working manifest. It commits nothing.

## What it reads

| Reference | Read in |
|---|---|
| `project-context.md` | Step 1: the configuration file, the context set, constraints, and conflicts |
| `manifest-update.md` | Steps 2 and 7: folder resolution, the Folder Identity Template, and the manifest |
| `voice.md` | Steps 1 and 5: the voice rules that open the constitution |

Each is a copy of `skills/human-docs/.ai-human-docs-reference/`, which started as a byte copy of the
research domain's source. **No check compares the two domains.** A change to the research domain's
`manifest-update.md` therefore leaves this skill on the old Folder Identity Template until someone
copies it here as well.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything; every reference is a file beside the skill. |
| `Skill` | The skill invokes no other skill. The report names a drafting skill only as an optional next step. |
| `NotebookEdit` | It writes Markdown only. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(date:*), Bash(mkdir:*), Bash(test:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(date:*)` | Step 2, today's date for a new folder's prefix, run rather than recalled. |
| `Bash(mkdir:*)` | Step 2, creating the folder when no name matches. |
| `Bash(test:*)` | Step 6, `test -e` on `outline.md`, so a replacement is announced before it is written. |

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
