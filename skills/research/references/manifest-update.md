# Manifest Update Reference

Shared instructions for updating the working manifest README after skill execution.

## Algorithm

After updating the folder's status, update the manifest README:

1. Resolve `<output_root>` from the `output_path` scalar in `.context/README.md` (default: `docs/working`). If the parsed value is not a string, print:

   WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`, please run `/ai-init` to set a custom output path."

   Do NOT block — this is a warning, not a hard gate. One root holds every folder: code features and documents alike.

2. Read the existing manifest at `<output_root>/README.md`
   - If it does not exist, create it with the template below

3. Scan the current folder's README.md:
   - Extract `title` from frontmatter (or H1 heading)
   - Extract description from the `## Description` section (first sentence only)
   - Determine state from the `## Status` checkboxes — use the LAST checked item, per the State Emoji Key below

4. Find the row for this folder in the manifest table and update it
   - If no row exists, append a new row (maintain alphabetical order — for `YYYY-MM-DD-` names this is also chronological order, oldest first; undated legacy rows sort after dated ones because digits precede letters in ASCII)
   - If the row exists and nothing changed, leave it alone

5. Update the "Last updated" date in the blockquote to today's date

6. Write the updated manifest back with the Edit tool (preserve all other rows unchanged)

## Manifest Template

```markdown
# Working Manifest

> Auto-updated by ai-skills pipeline. Last updated: <YYYY-MM-DD>

| Folder | State | Description |
|--------|-------|-------------|
```

## State Emoji Key

One ladder for every folder, regardless of whether the work is code or a document. The `## Status` list in the Folder Identity Template below is the only checklist this ladder reads.

| Emoji | State | Condition |
|-------|-------|-----------|
| 🆕 | Created | Has README only (no status item checked) |
| 🔬 | Research | `[x] Research` is the last checked item |
| 🛠️ | In progress | `[x] In progress` is checked, Complete is not |
| ✅ | Complete | `[x] Complete` is checked |

`✅ Complete` requires the explicit `[x] Complete` item. No skill checks it automatically — a human marks the work done.

## Row Format

```
| [<folder-name>](<folder-name>/) | <emoji> <State> | <first sentence of Description> |
```

## Folder Naming Convention

Every folder under the working root is named `YYYY-MM-DD-<inferred-name>` — an 11-character creation-date prefix followed by a kebab-case name derived from the work's description:

```
2026-08-01-api-rate-limiting
2026-08-01-quarterly-report
```

Three rules govern it:

1. **The date is the creation date.** It is written once, when the folder is made, and never rewritten. A later pipeline step running on a different day does not re-date the folder.
2. **The leading position is always the date.** Nothing else may occupy it — never a sequence number such as `001-` or `002-`. A working root that already contains sequentially-numbered folders holds legacy artifacts of another tool; do not imitate them. Chronological ordering comes from the date prefix, which sorts lexicographically, so a sequence number would add nothing and would displace the date.
3. **The 50-character truncation governs the inferred portion only.** The date prefix is added after truncation, so the longest name is 61 characters.

Obtain the date with `date +%F` rather than recalling it. A wrong-but-plausible date is invisible on inspection — nothing about `2026-07-31-foo` looks incorrect.

Existing undated folders are not renamed. They keep working; the resolution order below finds them by exact match.

## Folder Resolution Order

Given a name the user typed, resolve it in this order:

```
a. EXACT — if `<output_root>/<typed-name>/` exists, use it. Stop here.
b. DATED-SUFFIX — collect entries in `<output_root>/` matching `????-??-??-<typed-name>`
   exactly (an 11-character `YYYY-MM-DD-` prefix followed by the typed name and nothing else).
   - Exactly one match: use it. Tell the user which dated folder resolved.
   - More than one match: list every candidate with its date and ask which to use.
     Never silently pick one, and never pick the newest by default.
b2. ARCHIVE PROBE — before auto-creating, check `<output_root>/.archive/` for an
    exact or dated-suffix match on the same name. On a hit, tell the user the folder
    is archived, print the restore command
    (`mv <output_root>/.archive/<match> <output_root>/<match>`, or `git mv` if the
    working root is tracked), and ask whether to restore it or create a new folder.
    Never auto-create silently over an archived name.
c. AUTO-CREATE — only when neither (a) nor (b) matched, create
   `<output_root>/<today>-<typed-name>/`. Skills that do not create folders stop here and
   suggest `/ai-create` instead.
```

Step (a) first means a user who types the full dated name takes the cheapest path and never reaches the glob. Step (c) last preserves the forgiving auto-create the pipeline relies on — it just stops firing on a name that already exists under a date.

Step (b) is the step that carries the feature. Without it, a lookup miss on a short name becomes a brand-new empty folder while the real folder — holding the `research.md` or `plan.md` the run needs — sits beside it unread, and the run reports success.

The multiple-match branch asks rather than warning-and-continuing, which is the one place the pipeline blocks instead of degrading. Writing an artifact into the wrong feature's folder is not recoverable by reading a warning afterward.

Step (b2) exists because `/ai-archive` manufactures lookup misses. A folder it retires still holds the `research.md` or `plan.md` a later run needs, but the glob in step (b) enumerates `<output_root>/` only and never descends into `.archive/` — so without the probe, step (c) creates an empty twin over an archived name and reports success, which is the same failure step (b) was added to prevent. The probe hands the user a restore command rather than running one: un-archiving is deliberately not automated, so the decision to bring a folder back stays theirs.

## Folder Identity Template

The single README that `/ai-create` writes and every auto-creating skill reproduces. There is no code-vs-doc variant, so nothing downstream needs to detect which kind of work a folder holds.

The frontmatter `title` is the full dated folder name (`2026-08-01-api-rate-limiting`), matching the directory exactly. The H1 is the human-readable title and carries no date.

```markdown
---
title: <name>
---

# <Title>

## Description
<1-2 sentences: what this is and why it exists.>

## Requirements
<What must be true when this is done.>

## Scope
<What is in scope and what is explicitly out.>

## Affected Areas
<Code: paths and architectural layers touched. Documents: sources, systems, or subject areas covered.>

## Audience
<Who this serves — the users of the feature, or the readers of the document.>

## Status
- [ ] Research
- [ ] In progress
- [ ] Complete
```

`<name>` is the full dated folder name.

Fill every section with real content derived from the description and project context — not placeholders. Sections that do not apply to this folder's work get a one-line note rather than being deleted, so the shape stays uniform across folders.
