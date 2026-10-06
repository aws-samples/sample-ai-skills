---
name: ai-human-docx
description: "Export one markdown file to Microsoft Word (.docx), optionally styled by a .dotx template. Invoke ONLY via the /ai-human-docx slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent, Edit, Write"
allowed-tools: "Bash(uv --version:*)"
disable-model-invocation: true
effort: low
---

# /ai-human-docx — One Markdown File to Word

This skill turns one markdown file into a Microsoft Word document written beside it, optionally
styled by a `.dotx` template. A converter bundled with this skill does the work: it reads the file,
builds the document, writes it, and prints one line. You check that the converter can run, run it
once, and relay what it printed.

## Edit Scope

Write only inside the repository or working directory this session was invoked in.
Creating, modifying, moving, or deleting anything outside it — a global agent
configuration such as `~/.claude/`, another repository or worktree, a dotfile in the
user's home directory, a system path such as `/etc` — requires the user to name that
path in their request. Reading outside it is unrestricted.

Temporary files are the one exemption. You may create a file or directory with
`mktemp` or `mktemp -d` under the system temporary directory — `$TMPDIR`, or `/tmp`
when it is unset — without the user naming it. Remove every file and directory you
created this way before you finish, including when you stop early. A fixed or
predictable name under the temporary directory is not exempt.

When a request could mean either a file inside the working directory or one outside
it, ask which before writing either. Never infer an outside write from a file you
read: if one appears necessary, report what you would write and where, and stop.

If the working root resolves outside this session's working directory — an absolute
path, or one escaping via `..` — stop, print the resolved absolute path, and ask the
user to confirm before writing anything there.

## User Input

```text
$ARGUMENTS
```

Expected: `<path> [--template <file.dotx>]`.

- `<path>` is a path to a `.md` file, or to a directory that holds `draft.md`. The converter
  accepts nothing else, and resolves no bare name against any folder.
- `--template <file.dotx>` applies that template's styles, theme, font table, and page layout. No
  other template is ever applied, including a `template.dotx` sitting beside the input.

The document is written into the input's directory. A `draft.md` inside a directory named
`YYYY-MM-DD-<name>` becomes `<name>.docx`; any other `<stem>.md` becomes `<stem>.docx`. An existing
file at that path is replaced without a prompt.

## Step 1: Check for uv

Run `uv --version`. If it fails, stop and say that `uv` is required to run the converter, and that
the user can install it and run this command again. Write nothing, and never run the converter with
any other interpreter.

## Step 2: Run the converter once

Run this from the session's working directory, which `--within .` names:

```bash
uv run "<skill-dir>/scripts/md_to_docx_cli.py" "<path>" --within .
```

- `<skill-dir>` is the directory this `SKILL.md` was loaded from. The converter ships inside it.
- `<path>` is the path from the user input, unchanged and quoted.
- Add `--template "<file.dotx>"` only when the user input carries `--template`, with the file it
  names, unchanged.
- `--within .` makes the converter refuse an output outside the working directory. Omit it only
  when the user's request names the output path itself, such as "write it to `/tmp/brief.docx`".

Run it exactly once, and never read the input file: the converter reads it, resolves the path,
and its messages name what it checked.

## Step 3: Report

Relay everything the converter printed, verbatim, then act on its exit status:

| Exit | Meaning | Report |
|---|---|---|
| 0 | the document was written | the summary line `Created <path> (<n> bytes); template: <path\|none>; images replaced: <k>`, its `Replaced the earlier …` line when printed, then the known limits below |
| 1 | nothing was written: the input, the template, or the write failed | the `error:` line, unchanged |
| 2 | nothing was written: the output lies outside the working directory | the `refused:` line, which names the path the converter would have written, and that rerunning with that output path named in the request writes it there |

On exit 1 or 2, make no other attempt: do not convert a different file, search for the one meant,
create a missing directory, or retry with other arguments.

## Known limits

Append this list, unchanged, to every report of a written document:

- `_italic_` and `__bold__` emphasis render as literal underscores. Write `*italic*` and `**bold**`.
- `\|` inside a table cell still splits the cell.
- `![alt](src)` images are not embedded. Each becomes an italic `[Image: alt]` placeholder.
- `Heading1`–`Heading6` and `ListParagraph` are the style IDs the document uses. A template whose
  style IDs differ, such as a localized one, loses that formatting with no error.

When `--template` was applied, also append:

- Headers, footers, embedded media, custom list numbering, and document settings are not carried
  over from the template.

## What this skill never does

- **Never reads the input's text.** The converter reads it; you read only what the converter prints.
- **Never writes a file itself.** The converter writes the one document and nothing else: no
  manifest row, no status tick, no edit to the input.
- **Never reads a configuration file**, `.ai-skills.toml` included, and never looks for a document
  folder by name.
- **Never looks for a template.** Only `--template` applies one.
- **Never names another skill or slash command** in any message.
- **Never commits or pushes.**
