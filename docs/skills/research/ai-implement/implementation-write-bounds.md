---
title: "Implementation Write Bounds"
sidebar_label: "Implementation Write Bounds"
sidebar_position: 2
---

# Implementation Write Bounds

`ai-implement` is the only skill in the `research/` family that writes source code and runs
commands. The set of filesystem paths it may write during one run is **declared before the first
phase executes** and is derived from the plan it was handed. This page states how that set is
derived, which writes outside it are still permitted, and what to do when a run stops on a path the
plan never named.

The bound is prose the skill applies to itself. It is not a sandbox and does not claim to be one.
What it provides is that the intended footprint is stated before the writes happen and every
deviation is named afterwards — a crossing leaves a record. Beneath it sits a separate floor, owned
by the edit-scope constraint every writing skill carries: writes stay inside the current session's
repository. This bound narrows within that floor.

## The two parts of the declared write set

The set has exactly two parts, stated separately. Membership in one never authorises a write in the
other.

| Part | Source | Contents |
|---|---|---|
| Pipeline artifacts | `output_path` from `.ai-skills.toml` (default `docs/working`) and the resolved feature folder | Exactly three paths: `<feature-folder>/README.md`, `<feature-folder>/plan.md`, `<output_root>/README.md` |
| Source code | The plan's §5 "Files to Modify" | Everything derived by the expansion rules below |

The pipeline-artifact part is closed. No plan content widens it, and it needs no plan parsing — a
plan does not list the manifest row its own execution writes.

A §5 path that falls **inside** `<output_root>`, other than those three, is treated as a source-code
write governed by the manifest, and the run reports that the plan is writing into the pipeline's own
working root.

## Where the source-code part comes from

§5 "Files to Modify", and §5 alone.

Each phase of a plan also ends with a `Phase Spec (Paste-Ready)` block carrying a `Scope:` list.
Those blocks are handoff artifacts for external SDD tooling. They are **excluded** from write-set
derivation, for the same reason `ai-implement` already excludes them from task extraction: they can
be regenerated or edited independently of §5, and two lists claiming authority means the wider one
wins in practice, which is no bound.

They are used as a cross-check. A path present only in a handoff block is **reported as a
divergence** and is not admitted to the set.

## Expansion rules

§5 is a fenced ASCII tree grouped by purpose, not a flat manifest. Four rules expand it.

1. **The tree is walked, not read line by line.** An entry's path is its own segment joined to the
   parent segments its indentation implies. A `CREATE` or `MODIFY` marker is recorded and does not
   affect membership — both authorise a write. A tree root annotated as a repository rather than a
   directory (`my-repo/ ← this repository`) resolves to the repository root and contributes no path
   segment; a root naming a different repository is outside the bound entirely. A line carrying only
   wrapped annotation text, with no path segment of its own, is not an entry.
2. **Braces expand literally, at any segment.** `ai-create/{SKILL.md,references/}` becomes
   `ai-create/SKILL.md` plus the directory entry `ai-create/references/`. `skills/{adr,git}/README.md`
   becomes two paths.
3. **A directory entry authorises one level, not a subtree.** An entry ending in `/`, or naming a
   directory whose files are never listed, authorises files written *directly inside* it and nothing
   nested deeper. An entry whose children the tree *does* enumerate is a prefix and authorises
   nothing on its own — a `skills/` node with its contents spelled out does not authorise the skills
   tree.
4. **An entry resolving to neither a concrete path nor a bounded directory** is reported as
   unresolvable and is not in the set. It never widens to a prefix match.

## Read-only precedence

A path, directory, or repository the plan names as read-only, unchanged, or out-of-scope for writes
is **excluded from the set even when it sits beneath a directory the manifest otherwise authorises.**
Negative declarations outrank positive ones; a `CREATE` parent never rescues a read-only child.

Both forms count: an annotation inside the tree (`vendor/ ← READ-ONLY IN THIS WORK`) and a prose
sentence after it listing sources the work copies *from* and never writes *to*. `ai-plan`'s §5
template provides a stated place for both, so a plan does not have to invent its own phrasing.

## The extension rule

A path outside the declared set is written anyway, as a reported **extension**, when it satisfies
**both** of:

- **(a)** it sits beneath a directory the manifest names, **or** it is a companion the project's own
  conventions require for a named file — a co-located test, a package `__init__`, a lockfile a
  dependency install rewrites; **and**
- **(b)** writing it is necessary for a named file to function.

Both tests, not either. Test (a) alone would admit any file under a broad directory entry. Test (b)
alone would let "necessary" justify a path anywhere in the repository.

There is deliberately no fixed list of companion file kinds. Such a list is language-specific, it
dates, and it halts a run over a kind nobody thought to enumerate.

Every extension is named in the run's final summary as an extension of the declared set. The rule
is therefore a disclosure mechanism rather than a loophole: a plan extended twenty times reads,
visibly, as a plan whose §5 needs work.

The most common extension is the directory-only manifest entry. A §5 line reading
`tests/gates/ CREATE per-gate refusal tests` authorises the directory and names none of
the files inside it; each file written there is an extension, and each is listed.

## Commands

The bound covers paths a shell command creates, moves, or deletes — an `rm`, an `mv`, a
`git checkout`, a generator, an installer — not only paths written through a file edit. A command
whose effect on the filesystem cannot be confined to the declared set is not run.

## When a run stops on an out-of-set path

A path that is neither in the set nor an extension stops the run. The report names the path, quotes
the plan text the skill was acting on, and states what it would have written. It does not choose
between writing anyway and silently skipping the work.

**The fix is a §5 edit.** A stop means the plan under-declared its own footprint, which is common in
plans written before §5 was declared exhaustive. Add the path to §5 — inside the tree, grouped with
the purpose it serves — and re-run. Nothing else needs to change, and the run resumes with the path
authorised.

Two things not to do:

- **Do not add the path to a `Phase Spec (Paste-Ready)` `Scope:` block instead.** Handoff blocks
  never widen the set; the path will be reported as a divergence and the run will stop again.
- **Do not widen a directory entry to cover it.** A directory entry authorises one level only, so
  broadening `internal/tests/` to reach `internal/tests/mirror/fixtures/x` does not work, and a
  genuinely unrelated path should be named rather than hidden under a wider parent.

## Conflict gates with no human present

Two gates ask the user to arbitrate: the upfront batch in Step 2, and the mid-implementation gate.
Both have a defined behaviour for a run where nobody can answer — a non-interactive session, one
with permission prompts suppressed, or a tool call returning empty or defaulted: **write the full
conflict report and stop without implementing.** An unanswerable, empty, or defaulted answer is not
authorisation to pick a resolution.

A **contradiction** between plan and codebase — differing file contents, a non-matching interface or
signature, a dependency the plan assumes and the project does not declare — is a blocker by
definition, regardless of the skill's own assessment of whether it could work around it.

A plan merely **silent** on a detail is not a contradiction. The skill follows the project's existing
conventions and continues, as it always has. That distinction is what keeps the gate from firing on
ordinary ambiguity.

Suppressing permission prompts does not relax either the write bound or the conflict gates. Granting
the tools is not the same as authorising their use outside the declared set.
