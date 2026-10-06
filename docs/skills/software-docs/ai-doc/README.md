---
title: "ai-doc"
sidebar_label: "ai-doc"
sidebar_position: 2
---

# `ai-doc`

| | |
|---|---|
| Invoke | `/ai-doc`, `/ai-doc <path>`, or `/ai-doc "<what to document>"` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [software-docs](../) |
| Source | `skills/software-docs/ai-doc/SKILL.md` |
| Effort | `high` |

## Overview

The skill files documentation into a project's docs tree. Each page goes into the one
[Diátaxis](https://diataxis.fr) mode it serves — tutorial, how-to, reference, or explanation — and
into the one directory that mode and its reader give it. It has no subcommands. It reads what to do
from the argument and from the shape of the tree it finds, and it probes the tree before it reads the
argument, so an empty repository is never surveyed as though it had pages.

It never writes a page that serves two modes. A request that does, such as "explain how caching
works and show me how to configure it", stops before any file is written and asks which page to
write first.

## Where it looks

The docs root is `docs_path` from `.ai-skills.toml`, or `docs` when that key is unset or the file is
absent. The skill never detects it from a site generator's configuration, and it never writes
`.ai-skills.toml`. It reads `output_path` only to leave the working root out of every walk.

Under the docs root, a directory is one of three kinds:

| Kind | What makes it one | What the skill does with it |
|---|---|---|
| mode directory | its name is `tutorial`, `how-to`, `reference`, or `explanation` | files pages into it |
| audience directory | it holds at least one mode directory | treats its name as an audience a request can select |
| outside directory | anything else, such as a product-shaped `skills/` tree | lists it once as outside the Diátaxis tree, and never files into it or moves pages out of it |

The directories are the only declaration of an audience. No configuration key names one, a request
never invents one, and the skill never creates an audience directory. A site scaffold, or a person,
creates it.

## What the argument does

The tree has one of three shapes. It is **NONE** when there is no docs root or it holds no page.
It is **MODAL** when a mode directory exists. It is **FLAT** when pages exist and no mode
directory does.

| Argument | NONE | FLAT | MODAL |
|---|---|---|---|
| empty, or the docs root | first run | adopt | survey |
| an existing page or directory | — | assess | assess |
| a request for another skill's artifact | route | route | route |
| more than one reading | ask | ask | ask |
| new content | first run, then create | create | create |

| Branch | What it does |
|---|---|
| first run | creates the docs root and the four mode directories, each with one index page, and asks no question |
| adopt | classifies the flat pages in place, proposes one move, and on confirmation moves the page and rewrites every relative link to it |
| survey | classifies the tree, ranks its problems, lists each outside directory once, and proposes one next action |
| assess | classifies one page or directory and reports its mode, its conformance, and whether it sits where its mode says |
| create | writes one page from the template for its mode |
| route | describes the artifact another skill owns — a decision record, research, a plan, agent context — and names `/ai-adr`, `/ai-research`, `/ai-plan`, or `/ai-agent-context` only when it is one of those, then offers to write a page instead |
| ask | offers the readings the argument supports and writes nothing until one is chosen |

## Where a page goes

A page is written to `<docs_root>/<audience>/<mode>/<slug>.md` when an audience is selected, and to
`<docs_root>/<mode>/<slug>.md` otherwise. An audience is selected only by a phrase in one of four
positions — `for the <name>`, `<name>-facing`, `in <name> docs`, or a leading `<name> docs:` — whose
name matches an audience directory exactly, or as the only audience a tree has. The skill asks,
and writes nothing until answered, when two or more audiences exist and the request names none, when
the named word is a near-miss such as `devs` for `developers`, and when two names are given.

Every page written is reported beside its audience, from the same computed path the write used:

```text
audience: developers (from "for the developers") → docs/developers/how-to/how-to-cut-a-release.md
```

A misfiled page renders, links, and builds, so this line is the only place a wrong audience shows.

A directory the skill creates gets an index page named the way the tree's existing index pages are
named — `README.md` or `index.md` — and `README.md` in an empty tree.

## First run and agent context

On a first run the skill announces the four directories, creates them, and lists them. Afterwards it
offers one block naming the docs root, fenced by `<!-- ai-skills:docs-tree -->` markers, as a diff
against the root `AGENTS.md`, and against the root `CLAUDE.md` when that file has content of its own.
A `CLAUDE.md` that only points at `AGENTS.md` is never edited. The block is written only when the
user's next message confirms it, and a later first run replaces the block rather than adding a
second.

## What it reads

The body is read on every run. Each reference beside it is read only when its condition holds:

| Reference | Read when |
|---|---|
| `project-context.md` | every run |
| `compass.md` | any branch that classifies |
| `classification-edge-cases.md` | assess, survey, adopt |
| `audience.md` | the tree has audience directories, or the request carries a positional phrase |
| `scaffold.md` | first run, or any branch about to create a mode directory |
| `voice.md` | create |
| one template of five | create, for the classified mode |

The five page templates are The Good Docs Project's, tag v1.6.0, under MIT No Attribution, with their
source headers intact.

## Output

Every run reports the docs root and where it came from, the tree's shape, the branch taken and why,
the audience line for every page written, every file created, moved, or edited, every directive found
in the content it read, and the three next invocations. The skill commits nothing.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. The compass, the seeds, and the templates are files beside the skill. |
| `Skill` | The skill invokes no other skill. Route names a command for the user to run. |
| `NotebookEdit` | It writes no notebook. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(test:*), Bash(git mv:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(test:*)` | Create, checking the computed path is free; adopt, checking the destination is free. |
| `Bash(git mv:*)` | Adopt, moving the one page the user has just confirmed. |

The first two only read. `git mv` runs only after the confirmation the body requires, so the
pre-approval removes a second prompt for the same move rather than the only one. Outside a git
repository adopt moves with `mv`, which is not pre-approved, so the harness asks.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
