---
title: "ai-human-draft"
sidebar_label: "ai-human-draft"
sidebar_position: 3
---

# `ai-human-draft`

| | |
|---|---|
| Invoke | `/ai-human-draft <name> [instruction]`, with `--fresh`, `--headless`, a citation phrase, or HITL overrides such as `S1.B` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [human-docs](../) |
| Source | `skills/human-docs/ai-human-draft/SKILL.md` |
| Effort | `high` |

## Overview

The skill turns a document folder into `draft.md`, the delivered document: prose written for a
reader who did not commission it. The draft follows the folder's `outline.md` when there is one,
uses its `research.md` when there is one, and works from the folder `README.md` alone when neither
exists. When no folder matches the name, the skill creates one. It runs with no other skill
installed.

The draft is checked against a **constitution**: the voice rules of its `voice.md`, which are always
present, every `Constraints` bullet in the project context, and the document's own principles,
recorded in the folder README. Its principle count is never zero. When two context files state
constraints that one draft cannot satisfy together, or a document principle contradicts a project
constraint, the skill names both files, quotes both, and writes no `draft.md` until the user says
which applies.

## Two modes

The folder's state picks the mode, and the skill names it before writing.

| Folder state | Mode | What happens |
|---|---|---|
| no `draft.md` | fresh | a complete draft is written |
| `draft.md` exists | revise | the existing draft is changed only where an input requires it |
| `draft.md` exists, and `--fresh` | fresh | the existing draft is backed up and replaced by one carrying none of its text |

**Revise mode treats the whole existing draft as the user's text.** Nothing records which sentences
an earlier run wrote. Four inputs can require a change: a revision instruction in the arguments, a
section added, removed, or re-guided in `outline.md`, a finding or gap in `research.md` the draft does
not reflect, and a principle or voice violation found by a re-check of the whole draft. A new
section or a missing finding is added without touching the text around it. A change to existing
text — a section the outline dropped, a sentence the research now contradicts — is a conflict: the
skill quotes the text, says what the input requires, and recommends keeping the text. Each change is
an edit scoped to one section, never a rewrite of the whole file, so text no input touched is
byte-identical afterwards. A run with nothing to change writes nothing.

**One rolling backup.** Before any write over an existing `draft.md`, in either mode, the skill copies
it to `draft.prev.md`, replacing any earlier one. Only one generation is kept, so a second revising
run replaces the first backup.

## Where it looks

| Input | Source |
|---|---|
| the working root | `output_path` in `.ai-skills.toml`, or `docs/working`; the skill never writes that file |
| project constraints | the root `README.md`, `AGENTS.md`, and `CLAUDE.md`, then each `context_files` entry |
| document principles and citation mode | `### Principles` under the folder README's `## Scope` |
| identity, audience, and scope | the folder README's title, `## Description`, `## Requirements`, `## Audience`, and `## Scope` |
| structure and review choices | the folder's `outline.md`, when it exists |
| evidence | the folder's `research.md`, when it exists |

A short name binds to a dated folder: `onboarding-guide` finds `2026-09-02-onboarding-guide/`. When
more than one dated folder matches, the skill lists them and asks, and never picks by date.

**Document principles** sit under `## Scope`, not `## Requirements`, so a later outline run does not
read them as objectives. When the subsection is absent, the skill drafts two to four principles from
the README's description and audience and asks about each; principles it drafted are marked
` — *(inferred)*`. **The citation mode** — follow the stated constraints, cite every research claim,
or no citations — is asked on every run, defaulting to the last recorded answer, and is recorded as
a `Citations:` bullet beside the principles. A phrase such as `no citations` in the arguments
answers it. A citing draft uses inline prose links, never `[1]`-style markers, and never repeats a
research reliability grade; a weakly supported finding is worded as tentative instead.

**The outline's HITL Review block** is applied item by item. An override comes from an `Overrides:`
line in that block or from tokens such as `S1.B` in the arguments, which win. Every other item takes
its recommended choice, and the report lists those items.

## The interview

The skill asks rather than guesses, in rounds of one to four questions, and every question carries a
recommended option. The user can end the interview in any round, and `--headless` asks nothing.
Either way, a principle or a citation mode taken by default is marked ` — *(inferred)*` in the folder
README, and under `--headless` every conflicting passage of an existing draft is kept and listed in
the report. A question guarding a choice that a warning could not undo has **Stop** as its
recommended option: which of two dated folders to use, and which conflicting constraint applies.

## Output

The skill writes `<folder>/draft.md`, and `<folder>/draft.prev.md` whenever it changes an existing
draft. It edits the folder README only to record principles and the citation mode, and to check
`In progress` in its Status — never `Complete`. It updates that folder's row in the working manifest.
It commits nothing. Its report gives the mode, the principle count and where each principle came
from, the HITL items that took their default, each section changed and why, each conflict kept, and
every directive found in the folder's files.

## What it reads

| Reference | Read in |
|---|---|
| `project-context.md` | Step 1: the configuration file, the context set, constraints, and conflicts |
| `manifest-update.md` | Steps 2 and 10: folder resolution, the Folder Identity Template, and the manifest |
| `outline-format.md` | Step 3: the shape of `outline.md`, its HITL Review block, and the `Overrides:` line |
| `voice.md` | Steps 4, 7, 8, and 9: the voice rules that open the constitution, and the standard the draft meets |

Each is a copy of `skills/human-docs/.ai-human-docs-reference/`. `outline-format.md` describes the
format `ai-human-outline` writes, but `ai-human-outline` does not yet carry a copy of it, so **no
check compares the outline skill's own template with this reference**. A change to that template
needs the same change here, by hand.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything; every reference is a file beside the skill. |
| `Skill` | The skill invokes no other skill. The report names outline and export skills only as optional next steps. |
| `NotebookEdit` | It writes Markdown only. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(date:*), Bash(mkdir:*), Bash(test:*), Bash(cp:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(date:*)` | Step 2, today's date for a new folder's prefix, run rather than recalled. |
| `Bash(mkdir:*)` | Step 2, creating the folder when no name matches. |
| `Bash(test:*)` | Step 3, `test -e` on `draft.md`, which selects the mode. |
| `Bash(cp:*)` | Step 6, the backup to `draft.prev.md`, copied byte for byte rather than rewritten. |

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
