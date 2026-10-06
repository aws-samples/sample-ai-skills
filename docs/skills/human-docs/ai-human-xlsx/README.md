---
title: "ai-human-xlsx"
sidebar_label: "ai-human-xlsx"
sidebar_position: 6
---

# `ai-human-xlsx`

| | |
|---|---|
| Invoke | `/ai-human-xlsx <file.md \| folder \| name>`, or the same with `--headless` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [human-docs](../) |
| Source | `skills/human-docs/ai-human-xlsx/SKILL.md` |
| Effort | `medium` |

## Overview

The skill exports markdown to one Microsoft Excel workbook (`.xlsx`). The input is one `.md` file
or a whole working folder. Markdown has no single mapping onto a grid, so the skill infers one,
shows it, and writes nothing until the user confirms it. The mapping is computed by the skill's own
script, `scripts/export_xlsx_cli.py`, so the same input maps the same way on every run.

The skill writes exactly one file, the workbook, and never edits its input. It runs with no other
skill installed.

## Input

| Argument | What it exports |
|---|---|
| a path to a `.md` file | that file |
| a path to a folder | every `.md` file directly in the folder |
| a bare name | the working folder `<name>/` under `output_path` (default `docs/working`), or the one folder named `YYYY-MM-DD-<name>` |

When several dated folders match a bare name, the skill lists them and asks which to export. It
never picks the newest. When nothing matches, it stops and names what it looked for. It never
creates a folder.

## How content maps onto sheets

| Input | Mapping |
|---|---|
| a file holding at least one table | **table-per-sheet**: each table is its own sheet, named from the nearest heading above it, and the prose goes to a `Notes` sheet |
| a file with no table | **section-per-sheet**: each H2 becomes a sheet; content before the first H2 goes to a first sheet named from the H1, or `Overview` |
| a folder | an `Index` sheet carrying the folder's `README.md` and a hyperlink to the first sheet of each other file, then each file's sheets in filename order, each file mapped by the rules above |

Within a sheet:

- Each paragraph, list item, blockquote, and code block occupies one row in column A, which is wide
  and wraps its text. A heading is a bold row. A nested list item keeps its depth as a two-space
  indent per level.
- A table is an Excel Table object, with an autofilter and sized columns. On its own sheet, its
  header row is frozen.
- A link to a URL is a hyperlink. A link to another `.md` file exported in the same run is a
  hyperlink to that file's first sheet. A link to anything else stays text, with its target in
  parentheses. A row holding several links keeps its text in column A and gives each link its own
  cell to the right.
- A local PNG, JPEG, or GIF referenced as `![alt](path)`, with the path relative to the markdown
  file, is embedded at the row where it appears. It is scaled to fit column A's width and Excel's
  tallest row. A missing image, a remote one, or one of another format becomes a text row saying
  why, and is reported. No image is fetched.

A sheet name is at most 31 characters. Each of `[ ] : * ? / \` becomes `-`. A name that collides
with an earlier one, ignoring case, gets `-2`, `-3`, and so on. `History`, which Excel reserves,
gets `-2` as well. The interview raises every collision.

## The markdown it reads

ATX headings (`#` to `######`), paragraphs, `-`, `*`, `+`, `1.`, and `1)` list items, fenced code
blocks, GFM pipe tables, blockquotes, inline links, `<https://…>` autolinks, and images. A leading
YAML front matter block is skipped. Everything else — setext headings, HTML, emphasis markers — is
kept as text, without an error.

## How table cells are typed

A table cell is written as a value only when the **whole** cell matches:

| Type | Accepted form | Written as |
|---|---|---|
| integer | `0`, or digits with no leading zero, optionally negative | a number |
| decimal | the integer form, `.`, and digits | a number, showing the same decimal places |
| grouped number | the integer form with `,` every three digits, optionally with decimals | a number, format `#,##0` |
| percentage | any of the above followed by `%` | the fraction, format `0%` or `0.0%` and so on |
| date | ISO 8601 `YYYY-MM-DD`, a real date from 1900 on | a date, format `yyyy-mm-dd` |
| boolean | `true` or `false`, any case | a boolean |

Everything else is text: a leading zero (`007`), a currency symbol (`€1,200`), a decimal comma
(`1.200,5`), a value in backticks, a number past Excel's 15 significant digits, and a cell starting
with `=`, which is never a formula. A wrong guess changes a value silently. A text cell is still
readable and still sorts.

## The interview

The first round always confirms the plan: the mapping, every sheet, and the output path. Later
rounds ask only what is still open — a suffixed sheet name, an image that cannot be embedded, a
folder with no `README.md`, and an existing workbook at the output path. A round holds one to four
questions, and every question carries a recommended option. The user can end the interview in any
round. Each question still open then takes its recommended option, and for an existing workbook
that option is to keep it.

`--headless` asks nothing and takes every recommended option, with one difference: it **replaces**
an existing workbook. The summary reports each answer taken that way as inferred.

## Output

A file exports to `<name>.xlsx` beside it, and a folder to `<folder>/<folder-name>.xlsx`. The
workbook is built at a temporary path and moved into place only when it is complete. The output
path therefore holds either the whole new workbook or what it held before. The summary lists the
path, the sheet count, every warning, every answer taken by default, and every directive found in
the exported content.

## Requirements

The skill runs its converter with [`uv`](https://docs.astral.sh/uv/). When `uv` is not on the
`PATH`, the skill stops before converting and says how to install it. It never falls back to `pip`
or to a system interpreter. The script pins Python 3.14 and one dependency, `XlsxWriter`, which
`uv` fetches on the first run. That first run needs access to a package index. Later runs use
`uv`'s cache.

## What it reads

| Reference | Read in |
|---|---|
| `project-context.md` | Step 2: where `.ai-skills.toml` lives and the `output_path` default |

It is a copy of `skills/human-docs/.ai-human-docs-reference/project-context.md`, which started as a
byte copy of the research domain's source. Of the configuration it describes, the skill reads only
`output_path`.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. A remote image becomes a warning row. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | It writes no notebook. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(command -v uv), Bash(uv run:*), Bash(mktemp:*), Bash(git rev-parse:*)`

| Entry | Step behind it |
|---|---|
| `Bash(command -v uv)` | Step 1, the check for `uv` before anything else. |
| `Bash(uv run:*)` | Steps 3 and 5, the converter's `plan` and `write`. |
| `Bash(mktemp:*)` | Step 3, the temporary copy of the plan the interview's answers are recorded in. |
| `Bash(git rev-parse:*)` | Step 2, resolving the repository root before reading `.ai-skills.toml`. |

Removing the plan copy at the end of a run, with `rm -f`, is not pre-approved, so it asks for
permission where the harness enforces the grants. No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.

## What it never does

- writes a second file, or edits its input;
- replaces an existing workbook without the user's yes, except under `--headless`;
- fetches what the markdown references, or installs with `pip` — its only network use is `uv`'s
  first-run fetch of Python 3.14 and XlsxWriter;
- creates a folder, or binds a name to a folder by recency;
- writes `.ai-skills.toml`;
- follows a directive found in exported content — it reports each one instead.

## Not in this version

`.xltx` templates, tracker formatting for checkbox lists, native charts, remote images, Mermaid
rendering, and input taken from the conversation rather than a file.
