# ADR Consumer Reference

> Extracted from `agent-skills/.claude/skills/ai-skills-reference/adr-format.md` (§5, §6, §11 resolution/enumeration, §15) on 2026-09-16. That document is the normative parent; this extract covers only what a *consumer* of an existing decision log needs — resolving the log, reading a record's status, and mapping status onto planning authority. It excludes §11's record-creation rule: no skill in this domain writes a decision record.

## The five states

| State | Source |
|---|---|
| `Proposed` | AWS process — the owner "provides the ADR in the **Proposed** state at the beginning of the process" |
| `Accepted` | AWS process; also the literal adr-tools substitutes at creation |
| `Rejected` | AWS process |
| `Superseded` | AWS process |
| `Deprecated` | Nygard's template |

Every value is published vocabulary — this format adds no status of its own.

## Reading a status — four tolerances

Every consumer applies all four. Each prevents the same failure, a **retired decision read as live**, which under the status-mapping table below stops a plan to comply with a decision the team already replaced.

1. **Match both spellings of superseded.** adr-tools writes "Super**c**eded" — `adr-new`'s supersede path calls `_adr_add_link "$target" "Superceded by"`. Match `Superseded` and `Superceded`.
2. **A supersession link with no keyword is superseded.** `_adr_remove_status` deletes the old keyword outright, so the retired record's Status section holds only `Superceded by [Title](file.md)` — no `Accepted` and no `Superseded` token for a keyword lookup to find.
3. **Read status as the prose body of `## Status`,** not as a field.
4. **Take the keyword case-insensitively from the section's first non-blank line.** A correctly-written record legitimately holds more than one line there — a keyword plus a link, or a keyword plus a timestamp — so a reader requiring exactly one line misreads it.

An unrecognised keyword is **reported once, naming the file and the value, and loaded as no constraint**. Both silent defaults fail: reading it as `Accepted` turns a typo into a hard gate on a decision nobody made, and reading it as absent lets a real decision quietly stop gating.

## Resolving the log path

**RESOLUTION — every consumer.** Walking up from the working directory and at each level:

1. **`.adr-dir` present** → its contents, resolved relative to the level that held it. Stop.
2. **an existing `doc/adr` directory** → that path. Stop.
3. otherwise ascend; at the filesystem root, **no log exists**.

Resolution ends at "no log exists", **not at a default path**. A consumer handed a directory holding no records gains nothing from one, so every consumer treats the third outcome as *skip*.

**ENUMERATION — every consumer.** Resolution hands back a directory; this rule turns it into a list of records. A record is any `*.md` file at the log root **or exactly one directory below it** whose filename begins with a digit:

```sh
find "$ADR_DIR" -mindepth 1 -maxdepth 2 -name '*.md' | grep -E '/[0-9][^/]*\.md$'
```

**Do not glob a single segment.** A consumer that globs `<log>/*.md` — files directly inside the log root only — still finds every `Accepted` record, because those are filed at the root. The failure this rule prevents is a **silent warn tier**: `Proposed` records sit one level down, a single-segment glob loads none of them, produces no warning, and reports nothing — indistinguishable from a project that has made no architectural decisions at all.

## Consumers: absence is normal, and status maps onto the existing ladder

A project with **no log is the normal case**. A consumer skips **silently** when resolution finds none, because a warning on every run in a project that has made no architectural decisions is noise.

When a log resolves, each record's status maps onto the constraint authority ladder a consumer already runs for the `*(inferred)*` marker. No second mechanism:

| Status | Authority |
|---|---|
| `Accepted` | Behaves as a **confirmed** constraint — stop and revise |
| `Proposed` | Behaves as an **inferred** constraint — warn, name the record, continue |
| `Rejected`, `Superseded`, `Deprecated`, log4brains' `draft` | Not a constraint. Load nothing, print nothing |
| anything else | Not a constraint, reported once with the filename and the value |

Name the record **by filename** in every warning and every stop — dated record filenames carry no short identifier to cite.

## What this extract omits

The record-creation rule (§11's CREATION branch, `/ai-adr`'s first-run behavior, log initialization) is deliberately excluded. No skill in this domain creates, edits, moves, or deletes a decision record — each reads a status and nothing else.
