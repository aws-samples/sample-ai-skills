---
title: "ai-human-docx"
sidebar_label: "ai-human-docx"
sidebar_position: 2
---

# `ai-human-docx`

| | |
|---|---|
| Invoke | `/ai-human-docx <path>` or `/ai-human-docx <path> --template <file.dotx>` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [human-docs](../) |
| Source | `skills/human-docs/ai-human-docx/SKILL.md` |
| Effort | `low` |
| Needs | `uv` on the path. `uv` installs Python 3.14 when none is present |

## Overview

The skill exports one markdown file to a Microsoft Word document written beside it, optionally styled
by a `.dotx` template. A converter bundled with the skill, `scripts/md_to_docx_cli.py`, does all of
the work. It uses only the Python standard library, so it needs no other package and no network
access once `uv` has an interpreter. The agent checks that `uv` is present, runs the converter once,
and relays what it printed. The agent never reads the markdown file.

The skill needs no other skill installed. It reads no configuration file, writes no manifest row or
status, and names no other skill.

## Input

| Argument | Input |
|---|---|
| a path to a file ending in `.md` | that file |
| a path to a directory that holds `draft.md` | that `draft.md` |

Anything else stops the run before a file is written: no argument, a path that does not exist, a file
not ending in `.md`, or a directory with no `draft.md`. The message names the path the converter
checked. A bare name such as `quarterly-report` is never matched against a dated folder.

## Output

The document is written into the input's directory, under a name meant for the person who reads it:

| Input | Output |
|---|---|
| `docs/working/2026-08-01-quarterly-report/draft.md` | `docs/working/2026-08-01-quarterly-report/quarterly-report.docx` |
| `reports/q3/draft.md` | `reports/q3/draft.docx` |
| `notes/brief.md` | `notes/brief.docx` |

A `draft.md` whose directory starts with a `YYYY-MM-DD-` date loses that date in the file name. An
existing document at the output path is replaced without a prompt, and the report says so.

The converter writes a temporary file beside the output and renames it into place, so a run that fails
leaves an earlier export byte-identical. The agent passes `--within .`, so an output that would land
outside the working directory is refused: nothing is written, and the report names the path it would
have used.

A successful run reports one line:

```text
Created notes/brief.docx (3057 bytes); template: none; images replaced: 0
```

## Templates

A template is applied only when the request names one with `--template`. A `template.dotx` beside the
input, or anywhere else, is ignored. The document takes the template's styles, theme, font table, and
page layout. Headers, footers, embedded media, custom list numbering, and document settings are not
carried over. A template part that points at one of those, such as a header reference in the page
layout or an embedded font, is left out rather than copied with a reference to nothing.

A template that does not exist, is not a zip archive, or has no `word/styles.xml` that parses stops the
run before anything is written. The message names the template and the cause.

## What it renders

Headings `#` to `######` use the styles `Heading1` to `Heading6`. Paragraphs, bold, italic, bold
italic, strikethrough, inline code, links, horizontal rules, blockquotes, fenced code blocks, and pipe
tables render as their Word equivalents. Bullet and numbered lists render up to three levels deep.

| Markdown | Document |
|---|---|
| a numbered list with blank lines between its items | one list, numbered 1, 2, 3 |
| two numbered lists separated by a paragraph | the second list starts at 1 |
| YAML frontmatter at the top of the file | removed from the body; a `title:` value becomes the document's title property |
| `![alt](src)` | an italic `[Image: alt]` placeholder, counted in the report |

## Known limits

Every successful report lists these:

- `_italic_` and `__bold__` emphasis render as literal underscores. Write `*italic*` and `**bold**`.
- `\|` inside a table cell still splits the cell.
- Images are not embedded.
- The document uses the style IDs `Heading1`–`Heading6` and `ListParagraph`. A template whose style
  IDs differ, such as a localized one, loses that formatting with no error.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent, Edit, Write`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. The converter ships with the skill. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | It writes no notebook. |
| `Agent` | No step fans out. |
| `Edit`, `Write` | The converter is the only writer. Denying both makes "writes nothing but the document" hold at the tool level, not only in the body's prose. |

**Pre-approval set** — `Bash(uv --version:*)`

| Entry | Step behind it |
|---|---|
| `Bash(uv --version:*)` | Step 1, checking that `uv` is present. It only reads. |

The converter run is not pre-approved, so the first run asks. Its command line holds the absolute path
the skill is installed at, which differs from one machine to the next, and a command scope matches
text. Pre-approving `Bash(uv run:*)` instead would approve any script.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section and the converter's `--within` refusal are the controls on where it
writes.
