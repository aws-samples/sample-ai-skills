---
name: ai-archive
description: "Retire one finished work folder by moving it into the working root's .archive/ directory and transferring its manifest row. Invoke ONLY via the /ai-archive slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
allowed-tools: "Bash(date:*), Bash(mkdir:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git mv:*), Bash(mv:*)"

effort: medium
---

# Agent: Archive a Work Folder

You retire one finished folder from the working root. The folder moves to
`<output_root>/.archive/<name>/`, its row leaves the working manifest, and a row for it
appears in a second manifest inside the archive directory.

The working manifest gains a row per folder and never loses one, so the table meant to
answer "what am I working on" degrades into a project history. This skill is the only thing
that removes a row.

**This is the only skill in the set that performs a destructive, hard-to-reverse filesystem
mutation.** Every other skill writes a new artifact or edits one in place. There is no test
framework for skills, so nothing catches a wrong move after the fact. The safety is in the
three gates below — the status confirmation, the collision stop, and the tracking check —
and skipping any of them can lose a user's work.

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

Expected format: `<name-or-path>` — one folder per invocation.

## Step 1: Read the Context

Resolve `<output_root>` per `references/project-context.md` — read it rather than reconstructing its rules from memory: `output_path` from `.ai-skills.toml` at the repository root (default: `docs/working`). The file is optional, and its absence is silent.

Note in Step 10's report whether `<output_root>` came from `.ai-skills.toml` or from the default.

## Step 2: Resolve the Argument

If `$ARGUMENTS` is empty, list the folders under `<output_root>/` with their manifest states
and ask which to archive. Archive nothing until answered.

`$ARGUMENTS` is either a bare name or a path.

**A path** — anything containing a `/`. Resolve it and confirm it sits under
`<output_root>`. Reject anything outside with: "`<path>` is not under the working root
`<output_root>`. `/ai-archive` only archives work folders." Then stop. A path that resolves
to `<output_root>` itself, or to a file rather than a directory, is rejected the same way.
Strip any trailing slash before comparing, and reject a path whose resolved form escapes
the working root via `..`.

**A bare name** — apply steps (a) and (b) only of the Folder Resolution Order in
`references/manifest-update.md`. Read that reference rather than reconstructing the
order from memory.

**Do NOT apply step (c) AUTO-CREATE.** On no match, print "No folder in `<output_root>/`
matched `<typed-name>` by exact or dated-suffix match. Nothing was archived." and stop.
Creating a folder in order to archive it is nonsense, and the shared reference already
anticipates skills in this position: skills that do not create folders stop at step (b).

Call the folder that resolved `<name>` — it may carry a date prefix the user did not type.
Every path below uses it.

## Step 3: Check the Status

Read `<output_root>/<name>/README.md` and find its `## Status` section.

If `- [x] Complete` is present, proceed.

If it is absent, use AskUserQuestion. State which item *is* checked (or that none is), then
ask:

- "Archive anyway" — proceed to Step 4
- "Cancel" — stop, moving nothing

Archiving abandoned work is legitimate, so this is a confirmation and not a refusal. A
refusal would push the user to check `[x] Complete` falsely just to get past the gate, which
corrupts the one status item a human owns.

If the README is missing entirely, say so and ask the same question — a folder with no
identity document is more likely to be an accident than a finished piece of work.

## Step 4: Check for a Destination Collision

If `<output_root>/.archive/<name>/` already exists, STOP. Print:

```
`<output_root>/.archive/<name>/` already exists. Nothing was moved.
Rename one of the two folders and run /ai-archive again.
```

Never merge. A recursive move into an existing directory interleaves two folders' artifacts,
producing a folder whose `research.md` and `plan.md` came from different work — a corruption
that reads as success and is not recoverable by re-running anything.

## Step 5: Create the Archive Directory

```bash
mkdir -p <output_root>/.archive/
```

Run this before the move. `git mv` fails with `fatal: renaming ... failed: No such file or
directory` when the destination's parent is absent, so a first archive on a fresh project
fails without it. Verified.

The destination is always `<output_root>/.archive/`, inheriting the working root confirmed in
Step 1 — never a path computed from `$ARGUMENTS`. Step 2 guards the move's source against
escaping the working root; this is the same guarantee at its destination.

## Step 6: Select the Move Command from Tracking State

**This branch decides whether archiving preserves the work or destroys it.** It is a rule,
not a judgement call — do not substitute your own reading of "move the directory".

```bash
# 1. Is there a git repository at all? (fails outside a work tree)
git rev-parse --is-inside-work-tree 2>/dev/null

# 2. Is the source tracked? Exit 0 = tracked. Works on a directory pathspec.
git ls-files --error-unmatch "<output_root>/<name>" >/dev/null 2>&1
```

Then branch on the result:

```bash
# tracked (step 2 exits 0) — git records a rename; files survive every future checkout
git mv "<output_root>/<name>" "<output_root>/.archive/<name>"

# untracked, or no repository — nothing for git to record; a plain move is correct
mv "<output_root>/<name>" "<output_root>/.archive/<name>"
```

Plain `mv` on a **tracked** folder makes git record a **deletion**. After the next commit,
the archived content is absent from every future checkout — it survives only in history,
recoverable with `git show <commit>:<path>`, which is not what a user asking to "archive"
expects. Verified in a scratch repository: `git mv` produces
`R  .../2026-08-05-foo/research.md -> .../.archive/2026-08-05-foo/research.md` and the file
is present in a fresh clone; plain `mv` plus `git add -A` produces
`D  .../2026-08-05-foo/research.md` and the file is gone from the clone.

`git mv` needs no `-f` even when the destination is gitignored, which `.archive/` usually is.
Do not add it — `-f` would let the command overwrite an existing destination, and Step 4
exists precisely to stop that.

If `git mv` fails for any other reason, report the error and stop. Do not fall back to plain
`mv` — the fallback is the destructive path.

## Step 7: Remove the Working-Manifest Row

Find the folder's row in `<output_root>/README.md` and delete it with the Edit tool,
preserving every other row unchanged. The row looks like:

```
| [<name>](<name>/) | <emoji> <State> | <first sentence of Description> |
```

Capture the row's full text before deleting — Step 8 transplants it.

**If no row exists**, note it and continue. Report it in Step 10 as an unexpected condition
rather than treating absence as success. Nothing reconciles the manifest against disk, so a
folder that no skill ever registered is a real case — this repository has had two at once.
A silent partial success here would hide the inconsistency instead of surfacing it.

Update the "Last updated" date in the blockquote to today's date from `date +%F`.

## Step 8: Write the Archive Manifest

Create or update `<output_root>/.archive/README.md`:

```markdown
# Archived Work

> Folders retired from the working manifest. Last updated: <YYYY-MM-DD>

| Folder | State | Archived | Description |
|--------|-------|----------|-------------|
| [2026-08-05-foo](2026-08-05-foo/) | ✅ Complete | 2026-08-05 | First sentence of Description. |
```

The working manifest's three columns plus **Archived**. Transplant the captured row
verbatim and insert the archived date, obtained from `date +%F` — run it, do not recall it.

The row's link needs no rewriting. `[foo](foo/)` is relative to the manifest's own location,
so once the row lives in `.archive/README.md` it resolves to `<output_root>/.archive/foo/`
— correct as written.

The Archived column carries the only retirement date that exists anywhere. A folder name's
date prefix records **creation** and is never rewritten, so without this column nothing
records when a folder stopped being active and the archive table sorts by an increasingly
irrelevant key.

If the row was missing from the working manifest, build one from the folder's README —
title, state from its `## Status` per the state-emoji key in
`references/manifest-update.md`, and the first sentence of its `## Description`.

Maintain alphabetical order in the table (for `YYYY-MM-DD-` names this is also chronological
order, oldest first; undated legacy rows sort after dated ones because digits precede letters
in ASCII). Update the "Last updated" date. Preserve all other rows unchanged.

**The state does not change.** The ladder is 🆕 → 🔬 → 🛠️ → ✅ and there is no archived
state. Archiving changes a folder's *location*, so the row moves between two manifests
carrying whatever state it already had. Never check `Complete` on the folder's behalf —
only a human does that.

## Step 9: Do Not Update the Folder's Status

This skill writes nothing inside the archived folder. It does not check a status item, add
an archived marker, or edit the README. The folder is retired as-is, so that restoring it is
a move in one direction with nothing to undo.

## Step 10: Report

Tell the user:

```
Archived: <output_root>/<name>/  →  <output_root>/.archive/<name>/
Move command: <git mv | mv>  (<source was tracked by git | source was untracked | no git repository>)
Working manifest: row removed
Archive manifest: row added with Archived date <YYYY-MM-DD>

To restore:
  <git mv | mv> <output_root>/.archive/<name> <output_root>/<name>
```

Then report anything unexpected, each on its own line:

- the working manifest had no row for this folder
- the folder's Status did not show `[x] Complete` and you confirmed
- the folder had no README.md

If none applies, say the run was clean. Do not omit this section — the missing-row case is
the one a user would otherwise never learn about.

Print the restore command with the same command the move used: a tracked working root wants
`git mv` back, an untracked one wants plain `mv`. There is no `/ai-unarchive`; this line is
the whole restore path.

## What This Skill Does NOT Do

- **No un-archiving.** Restoring is the move in the other direction, and Step 10 prints the
  exact command. Wrapping a one-line `mv` in a second skill buys nothing.
- **No archiving of individual artifacts.** This moves whole folders. A separate nested
  `.archive/` pattern exists inside some work folders, retiring superseded artifacts *within*
  a live folder — a different thing, and not what this skill does.
- **No bulk form.** One folder per invocation. No multiple names, no "archive everything
  complete" sweep.
- **No compression or pruning** of archived content. The bytes move unchanged.
- **No manifest reconciliation.** The skill reports a missing row (Step 7) but does not
  sweep the whole table against disk.
- **No fifth status state.** See Step 8.
