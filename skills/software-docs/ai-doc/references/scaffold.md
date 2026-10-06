# Scaffold: Index Pages and the Agent-Context Block

What a run writes when it creates a mode directory, and the one block FIRST RUN offers to the root agent-context files. Read this file on FIRST RUN, and on any other branch about to create a mode directory.

## 1. The index file name follows the tree

Every directory this skill creates gets exactly one index page, written in the same step, because git does not track an empty directory and a generated sidebar over an empty one fails a site build. Its name is decided by the index pages already under the docs root, outside the working root and the excluded directories:

- **every existing index is `README.md`, or there is none** → `README.md`;
- **every existing index is `index.md`** → `index.md`;
- **both names are in use** → the name more directories use, and `README.md` on a tie.

Never create an index page in a directory that already holds either name. Writing the other name would give that directory two index candidates, and a site generator then serves one of them without warning.

## 2. The four mode index pages

Write each seed exactly, changing only three things:

- **`sidebar_position`**: the mode's order — tutorial 1, how-to 2, reference 3, explanation 4 — when the directory sits directly under the docs root. Under an audience directory, add the number of audience directories to it, which is the numbering a site scaffold uses so that each audience's own index sorts ahead of its modes.
- **Sibling links**: each seed links its sibling modes as `../<mode>/README.md`. Write the index name from section 1 in place of `README.md`. Keep a link only when that sibling mode directory exists at the same level once this step completes; otherwise replace the link with its plain text, because a link to a missing directory fails a site build that treats broken links as errors.
- **Extension**: always `.md`, never `.mdx`. An `.mdx` file is compiled as MDX, where a brace starts an expression.

The worked example in each seed sits in a fence on purpose: fence-aware heading extraction ignores it, so the index page does not read as a page of that mode.

### `tutorial/`

````markdown
---
title: "Tutorial"
sidebar_label: "Tutorial"
sidebar_position: 1
---

# Tutorial

Guided lessons for a reader who has not used this project before. A tutorial's job is to give them a first success, so it makes every choice on their behalf and follows one path from start to finish — no options, no branches, nothing to decide. What the reader learns is the shape of the thing; the exercise itself can be small.

A tutorial is a lesson, so it says what the reader will build and takes them through it:

```markdown
# Build your first report

By the end of this tutorial you will have a working report and will have used
the query builder, the formatter, and the export step.
```

Nothing here explains *why* the system works as it does — that belongs in [explanation](../explanation/README.md) — and nothing here assumes a goal the reader brought with them, which is what a [how-to guide](../how-to/README.md) is for.
````

### `how-to/`

````markdown
---
title: "How-to"
sidebar_label: "How-to"
sidebar_position: 2
---

# How-to

Directions for a reader who already knows what they want to accomplish. Each guide assumes a goal and shows the shortest reliable route to it. Nothing here teaches the system from scratch — that is the [tutorial](../tutorial/README.md).

A how-to title begins "How to", so it says exactly what the guide shows:

```markdown
# How to configure connection pooling
```

For the reasoning behind a design, see [explanation](../explanation/README.md).
````

### `reference/`

````markdown
---
title: "Reference"
sidebar_label: "Reference"
sidebar_position: 3
---

# Reference

Descriptions of the project's interfaces and behaviour, for looking something up mid-task. Reference mirrors the product rather than any workflow, so these pages are organised the way the thing itself is organised. Come here for a specific fact and leave with it.

Reference is austere and states what is, without instructing:

```markdown
## `--timeout`

Seconds to wait before abandoning a request. Integer, default 30. A value of 0
disables the timeout.
```

Reference can describe how something works. What it does not do is walk a reader through a task — that is a [how-to guide](../how-to/README.md) — or argue for a design, which is [explanation](../explanation/README.md).
````

### `explanation/`

````markdown
---
title: "Explanation"
sidebar_label: "Explanation"
sidebar_position: 4
---

# Explanation

Why the project is built the way it is, and what the alternatives were. These pages are for understanding rather than doing: read them to find out why a convention exists, or when a decision looks arbitrary and the reasoning would help. Nothing here is needed to get a task done.

An explanation title reads naturally after an implicit "About", and the page discusses rather than instructs:

```markdown
# About the permission model

Permissions are checked at the boundary rather than per record. That trades
some flexibility for a guarantee that no code path can skip the check.
```

For the steps to do something, see [how-to](../how-to/README.md). For what a setting does, see [reference](../reference/README.md).
````

## 3. The agent-context block

FIRST RUN offers one block that tells an agent where the docs tree is. It is fenced by two HTML comments, which are stripped before an agent-context file is loaded, so the markers cost nothing in context and let a later first run find and replace the block:

```markdown
<!-- ai-skills:docs-tree -->
## Documentation tree

This project's documentation lives in `docs/`, sorted by [Diátaxis](https://diataxis.fr) mode: `tutorial/` holds lessons for a newcomer, `how-to/` holds steps toward a goal the reader already has, `reference/` holds descriptions to look up, and `explanation/` holds the reasoning behind the design. A page serves exactly one mode; when a page starts serving two, split it rather than adding a section.

A person files a new page with `/ai-doc "<what to document>"`, which chooses the mode and the path. When you write a page directly, put it in the directory of the mode it serves. A how-to title begins "How to"; an explanation title reads naturally after an implicit "About".
<!-- /ai-skills:docs-tree -->
```

Write the literal resolved docs root in place of `docs/`. The block is a prose pointer: never an `@path` import, which would load the tree into every session at launch, and never an absolute path.

**Where it goes.** Into the repository root's `AGENTS.md`, created if absent. Also into the root `CLAUDE.md` when that file exists and is **not a pointer**. A pointer is a `CLAUDE.md` whose content, with every HTML comment removed and surrounding whitespace trimmed, is exactly `@AGENTS.md`. Never edit a pointer: it would stop being one, and a tool that deletes pointers before deployment refuses to delete anything else. Never write a `CLAUDE.md` or an `AGENTS.md` inside the docs root, where a site generator would publish it as a page.

**Replace, never duplicate.** When a file already holds the two markers, replace everything from the opening marker to the closing one, inclusive. A file ends a run holding exactly one fenced block.

**Offered, never asked.** FIRST RUN asks no question, and the block does not change that. After the run's report, show the change to each target file as a diff, say that neither file has been written, and end the run. Write the block only when the user's next message confirms it, then list each file written. Do not use a question tool for this offer.

**On decline**, or with no confirmation, write nothing and say that the tree exists but no agent will be routed to it, so a page an agent writes may land outside it.
