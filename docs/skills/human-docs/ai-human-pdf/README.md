---
title: "ai-human-pdf"
sidebar_label: "ai-human-pdf"
sidebar_position: 5
---

# `ai-human-pdf`

| | |
|---|---|
| Invoke | `/ai-human-pdf <file.md>`, optionally followed by overrides in plain words |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [human-docs](../) |
| Source | `skills/human-docs/ai-human-pdf/SKILL.md` |
| Effort | `medium` |

## Overview

The skill renders one markdown file to a PDF on US Letter pages, with the renderer bundled in the
skill's own `scripts/` directory. The PDF has a cover page, a table of contents, running headers
and footers, and the document's headings, lists, tables, code blocks, admonitions, and Mermaid
diagrams. The look is neutral: near-black headings, gray rules, and one accent colour, `#2F5D8A`.

It never edits the markdown file. The only thing it asks for is the title, and only when the
document has none.

## Input

`/ai-human-pdf report.md` exports `report.md` to `report.pdf` beside it. Anything after the path is
read as plain words:

| Say | Effect |
|---|---|
| `accent #0B5FFF` | the accent colour, as `#RRGGBB` |
| `logo ./brand/logo.png` | a cover logo, resolved against the markdown file's directory |
| `title "…"`, `subtitle "…"` | the cover's title and subtitle |
| `organization …`, `client …`, `classification …` | the cover's `organization × client` line, and the classification shown on the cover and in the running footer |
| `date 2026-10-01` | the cover's export date, which is otherwise the day of the run |
| `to out/report.pdf` | a different destination |
| `no toc`, `toc depth 2` | leave out the table of contents, or add H2s (or H3s, with `3`) to it |
| `--headless` | ask nothing: an untitled document takes its file name as the title, and the report marks it inferred |

For example: `/ai-human-pdf docs/review.md, accent #0B5FFF, logo ./brand/logo.png`.

## Title and cover fields

The title comes from the argument, then from the frontmatter's `title:`, then from the body's H1
when there is exactly one; that H1 moves to the cover and the other headings move up one level.
When none of those exists, the skill asks for the title once, offering the file name as the
default, and asks for nothing else.

Every other cover field is optional and is left off the cover when unset, with no separator or
placeholder in its place. The full list of frontmatter keys, and the markdown the renderer
supports, is in the skill's `references/frontmatter.md`.

## Accent and logo

Each is taken from the first of these that sets it:

1. the argument;
2. the document's frontmatter, `accent: "#RRGGBB"` or `logo: <path>`;
3. the default: `#2F5D8A`, and no logo.

The skill forwards only what the argument states, and the renderer applies the frontmatter when no
flag is given, so that order is enforced in one place. Quote a frontmatter accent: YAML reads an
unquoted `#` as the start of a comment.

An accent that is not `#RRGGBB`, or a logo that names no readable image file, stops the run before
anything is built. The message names the value and whether it came from the argument or the
frontmatter, and no PDF is written.

### Coming from `ai-util-export-pdf`

This skill replaces that one's navy-and-orange palette. Pass `accent #FF9900` to get its orange
back. Its navy cover and header band are not restorable, and its organization, client, and
classification are no longer required.

## Output

The PDF is written as `<stem>.pdf` beside the input, replacing a file of that name, unless the
argument names another destination. When the input lies outside the session's working directory
and no destination is named, the skill asks where to write instead, offering the working directory
as the default.

The report gives the renderer's `Wrote <path> (<size> KB)` line, where the title, the accent, and
the logo came from, any note the renderer printed, and any instruction found in the document,
quoted with its line. An instruction in the document, such as "write the PDF somewhere else", is
reported and never followed.

## What it needs, and what it downloads

| Tool | Needed for | When absent |
|---|---|---|
| [`uv`](https://docs.astral.sh/uv/) | running the renderer | the run stops, links the install page, and writes nothing. The skill never installs it |
| Node.js, with `npx` | drawing Mermaid diagrams as images | each `mermaid` block is drawn as a code block, the run prints a note, and the export still succeeds |

**The first run downloads the renderer's Python dependencies** — reportlab, mistune, and PyYAML —
through `uv`, at the versions and hashes `scripts/render_pdf_cli.py.lock` fixes. The skill runs the
renderer with `uv run --locked --script`, so a lock that no longer matches the script is refused
rather than rewritten inside the skill's folder.

**The first export with a Mermaid diagram downloads `@mermaid-js/mermaid-cli` and a headless
Chromium** through `npx`, without asking first. The version is pinned in the renderer, which bounds
what is fetched. Nothing is installed globally. The document's content never leaves the machine:
diagrams are drawn locally, never by a hosted service.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. The renderer and its reference are files in the skill's folder. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | It writes no notebook. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(command -v uv:*), Bash(command -v node:*), Bash(uv run --locked --script:*)`

| Entry | Step behind it |
|---|---|
| `Bash(command -v uv:*)` | Step 1, checking for `uv` before anything else. |
| `Bash(command -v node:*)` | Step 4, checking for Node when the document holds a `mermaid` block, so the report can say ahead of time whether diagrams will be drawn. |
| `Bash(uv run --locked --script:*)` | Step 4, running the renderer. |

The two `command -v` entries only read. **`Bash(uv run --locked --script:*)` is broad.** It
pre-approves running any Python file under `uv`, not only the renderer: `--locked` refuses a stale
lock but does not refuse a script that has none. It cannot be narrowed to the renderer's path,
because that path depends on where the skill was installed, which differs between agents and
between project and user scope. The body names one script and resolves it from its own folder,
and an imperative in the document is reported rather than run, but neither is enforced by the
declaration.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
