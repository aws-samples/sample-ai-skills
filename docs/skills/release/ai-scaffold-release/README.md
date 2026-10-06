---
title: "ai-scaffold-release"
sidebar_label: "ai-scaffold-release"
sidebar_position: 3
---

# `ai-scaffold-release`

| | |
|---|---|
| Invoke | `/ai-scaffold-release` |
| Activation | slash command, or when a request matches the skill description |
| Domain | [release](../) |
| Source | `skills/release/ai-scaffold-release/SKILL.md` |

## Overview

Configure a repository's release path. Two halves, installed separately and never as a side effect
of one another:

- **internal** — version derivation from Conventional Commits, a git-cliff configuration, a release
  script, a forge-release script, CI jobs, and a local bootstrap tag.
- **promote** — publish one chosen tag's filtered tree to a public target.

Which half is installed is decided from `references/release-modes.md` **before** the probe runs, and
the decision is stated before any other output. An ambiguous request installs the internal path only
and names the phrasing that would have installed the other.

## When to use it

Use when a repository has no release machinery yet, or when asked to set up releases, versioning, or
a changelog. Ask for a **public publish path**, or to **promote releases publicly**, to get the
second half — no phrasing of a request for the first installs it.

## The internal half

| Writes | From |
|---|---|
| `cliff.toml` | `assets/cliff.toml` |
| `scripts/release_cli.py` | `assets/release_cli.py` |
| `scripts/gitlab_release_cli.py` (GitLab only) | `assets/gitlab_release_cli.py` |
| `Makefile` targets `release-preview`, `release` | delegate to `uv run scripts/release_cli.py` |
| CI job or workflow | `assets/gitlab-ci-release.yml` / `assets/github-release.yml` |
| `.gitattributes` lines fixing `cliff.toml` and `scripts/*_cli.py` at LF | — |
| one local annotated bootstrap tag, never pushed | — |

After the internal half is written, and only with confirmation, the skill appends a commit-convention block, composed from
`references/commit-convention.md`, to the repository's `CLAUDE.md` or `AGENTS.md`. With no way to
ask, it refuses: it prints the block and the command that authorizes it, and leaves the file
unchanged.

## The promote half

| Writes | From |
|---|---|
| `scripts/promote_cli.py` | `assets/promote_cli.py` |
| `.promote-target` | `assets/promote-target.template` |
| CI job or workflow | `assets/gitlab-ci-promote.yml` |
| `scripts/github_release_cli.py` (GitHub target only) | `assets/github_release_cli.py` |

`.promote-target` carries three keys — `PUBLIC_TARGET`, `PUBLISH_PATHS` (one line per path),
`PUBLISHER_IDENTITY` — and is **parsed as `key=value`, never sourced**, so nothing in it can
authorize a push. The confirmation is read from the environment only.

**Three refusals**, all of them before the temporary worktree exists:

1. the configuration is absent;
2. `CONFIRM_SHA` is not the object id of the tag being promoted;
3. `PUBLISH_PATHS` does not describe the tag's tree.

The third has four forms and they are one refusal, because they are four answers to one question: an
entry names a path the tree does not contain, an ancestor component of it is a file rather than a
directory, an ancestor entry already ships it whole, or it is malformed — a leading or trailing
separator, an empty component, or a `.` or `..` component. A malformed entry is refused before any
tag is resolved, since its fault needs no tree to see.

A fourth check is a precondition rather than a policy: the tag must exist on origin as an annotated
tag, which is also what keeps a never-pushed bootstrap tag unpublishable. A confirmed run also needs
the target to be readable, because the public commit is built on the target's own tip.

**No internal history is published.** The public commit is written from the filtered tree with
`git commit-tree`. Its author and committer are the publisher identity, its message is `Promote <tag>`,
and its only parent is a commit the target already holds — or none, when the target has no branch.
The dry run names that parent on a `parent:` line.

**Withholding is by absence from an allowlist of paths, and the allowlist binds at every depth.** A
path's own name never withholds it; an entry may name a directory or a single file at any depth, with
no depth limit; and the skill proposes no allowlist — it prints the tag's tree recursively, in one
invocation, and asks. Naming two descendants of a directory and not the directory publishes it
**partially**: the named descendants ship and every unnamed sibling is withheld by the same absence.
The dry run names what each descended level left behind, under a `withheld under <dir>:` heading,
because a partially published directory is where the allowlist's accepted failure mode — a new page
silently not shipping — otherwise hides. `scripts/history_probe_cli.py` is an optional configure-time
audit of what withheld paths held in history, which a promotion does not publish, and it is never
written into the target repository.

**The floor, with no repository gates configured**, is a confirmation that cannot be skipped and a
lease that is never overridden: one `git push --atomic --force-with-lease` with no fallback, expecting
the tip the public commit was built on. That tip is the one this clone last promoted, when the clone
holds that record. Otherwise it is the target's current tip, adopted as the parent — which is what
every CI run does, since a fresh clone holds no record — so there a commit someone else put on the
target is built on rather than refused. A tip that moves between the run's read and its push
refuses the run.

**Two optional extension points, both absent from a fresh install** — no stub file, no gate
directory, no commented-out gate list:

| Extension point | Shape |
|---|---|
| `scripts/promote-gates.sh` | executed (never sourced) after the confirmation and before any push, with `TAG` and `PUBLIC_TARGET` exported; non-zero refuses |
| `needs:` on the promote job | a scan, policy service, or approval the pipeline already runs |

The six refusals the base does not carry — origin pairing, tip-parent ancestry, divergence, the
history-exposure gate, the content scan, and the two acknowledgements — each keep a forwarding
address in `references/promote-extensions.md`, naming what the check did, why only the installing
repository can state that policy, and the shape of the replacement.

## Invoking a promotion

Configuring and promoting are separate acts; installing the promote path promotes nothing.

The script is run through `uv` by its own path — `scripts/promote_cli.py` as installed, wherever
the repository moved it otherwise:

```
uv run <promote_cli.py> [TAG]                             # dry run — reports, pushes nothing
CONFIRM_SHA=<tag object id> uv run <promote_cli.py> TAG   # promotes
```

There is no `--dry-run` flag: omitting `CONFIRM_SHA` is what makes a run a dry run. `CONFIRM_SHA` is
distinct from the internal path's confirmation and neither satisfies the other. Every dry run prints
the tag, its tag object id, the commit it points at, the target, the paths that ship, the paths
withheld, whether a repository gate hook is present, and the exact confirmation to re-run with.

The confirmation is the **tag object's** id, in full. A tag object records its name, its commit,
and its annotation, so a tag deleted and re-pushed, force-moved, or re-cut with a different
annotation after the dry run has a different id and the confirmed run refuses. The commit id is
refused, because it does not cover the annotation, which is published as the public tag's message.
The tag's name and an abbreviated id are refused too, and each refusal prints the id to use.

## A GitHub target gets a Release

GitHub creates no Release object for a pushed tag. When the target's host is `github.com`, and the
builder confirms that classification, the skill installs `scripts/github_release_cli.py` and the job
runs it after `promote_cli.py`, in the same job and for the same tag. Its body is the tag's annotation,
byte for byte, and it is created with `make_latest=legacy`, so backfilling an older tag leaves the
newer Release marked latest. Any other target gets no Release step.

The script follows `promote_cli.py`'s confirmation rule: with no `CONFIRM_SHA` it prints the Release it
would create and contacts no host. It is safe to re-run, and it never edits a published Release:

| On the target | What a confirmed run does |
|---|---|
| no Release for the tag | creates it |
| a Release with an identical body | reports success and writes nothing |
| a Release with a different body | refuses and prints the difference |
| no such tag | refuses, because GitHub would create the tag at the default branch's tip |

**One token authorizes both steps.** A GitHub fine-grained token with **Contents: Read and write** on
the target repository, set as the masked, protected CI variable `PROMOTE_TOKEN`, authorizes the push
and the Release. The job writes it to a credential-helper file, never into a URL. A deploy key cannot
create a Release, and an organisation may have to approve a fine-grained token before it works.
From a workstation, the script falls back to `GITHUB_TOKEN`.

**Scope the credential to the promote job.** On GitLab, the installed `public:promote` declares the
environment `public`, with `action: access`, which records no deployment. Set the credential
variable's environment scope to `public`, and only that job receives it. No other job in the
pipeline, and none of the third-party code those jobs run, holds write access to the public target.
A variable left at the every-environment scope `*` still works, but every job receives it. The skill
reports this setting and cannot make it.

**If the Release step fails after the push, do not re-run the promotion.** Its new public commit
would have the pushed one as its parent, so the new tag object differs and the push is refused.
Create the Release by hand instead, with the command the script prints:

```
CONFIRM_SHA=<tag object id> PROMOTE_TOKEN=… uv run scripts/github_release_cli.py v0.4.0
```

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`forge`, `web_host`, `ssh_host`, `project`, `project_id`, `cli`, `exposure`, and `public_target`. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. A
recorded `gitlab` classifies a self-managed instance that has no `.gitlab-ci.yml` yet.
[`ai-scaffold-dev-context`](../../dev/ai-scaffold-dev-context/) records every key at once.

## Tool grants

This skill carries the only denials in the repository that do real security work, because its body
makes an explicit negative claim and these declarations make that claim structural instead of merely
written down. Elsewhere in the repository the denial sets remove network reach, skill invocation and
unused fan-out — all real, none of it touching the capability that carries the risk.

Its body states, at Step 6: **"Do not push this tag, a branch, or a release object."** The promote
half adds a second negative claim at Step 7c: installing the promote path promotes nothing, and every
push lives in the installed `scripts/promote_cli.py` rather than in the document.

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent, Bash(git push:*), Bash(git send-pack:*), Bash(gh:*), Bash(curl:*)`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | The body routes between its own two halves; it never invokes another skill. |
| `NotebookEdit` | The files it writes are a TOML config, Python scripts, a `Makefile`, CI configuration, and a `key=value` configuration file. |
| `Agent` | No fan-out step. |
| `Bash(git push:*)` | The no-push claim's most obvious spelling. |
| `Bash(git send-pack:*)` | The plumbing command that pushes without the word `push`. |
| `Bash(gh:*)` | A release object can be published through `gh` — `gh release create`, or `gh api` — with no `git push` anywhere. |
| `Bash(curl:*)` | The same, through arbitrary HTTP against the forge's REST API. |

**Four entries rather than one, and that is the actionable part.** `ai-scaffold-release`'s job is to
create a release and to configure a path that publishes one. A single tidy `Bash(git push:*)` would
leave the no-push promise holed exactly where the skill's real work lives, because the forge's release
object never needs `git push` to reach it.

**The `gh` denial is bare rather than scoped, and that cost a step a command.** It was previously
`Bash(gh release:*), Bash(gh api:*)`, scoped so that the credential pre-flight could consult
`gh auth status`. The promote half denies the forge CLI as a capability rather than two of its
subcommands, so that pre-flight can no longer run it: Step 4 now reports the presence of
`GITHUB_TOKEN` and names `gh auth status` as the operator's own check. That is a real reduction in
what the pre-flight verifies, accepted deliberately — a skill that can configure a public publish
path should not also be able to publish a release object, and two scoped entries could not close
every subcommand that does.

**Pre-approval set** — `Bash(uv --version:*), Bash(test:*), Bash(git remote:*), Bash(git tag:*), Bash(git log:*), Bash(git ls-remote:*), Bash(uv run scripts/promote_cli.py:*)`

| Entry | Step behind it |
|---|---|
| `Bash(uv --version:*)` | Step 0, the check that `uv` is installed, before anything else runs. |
| `Bash(test:*)` | Step 4's credential pre-flight, testing for `CI_JOB_TOKEN`, `GITLAB_TOKEN` or `GITHUB_TOKEN`. Presence is reported; a value never is. |
| `Bash(git remote:*)` | Step 2.1, `git remote get-url origin` → forge topology. |
| `Bash(git tag:*)` | Step 2.2's `git tag --list`, and Step 6's `git tag -a` plus its `git tag -l` verification. |
| `Bash(git log:*)` | Step 2.4, `git log --format=%s` → how many existing subjects the parser would group. |
| `Bash(git ls-remote:*)` | Step 6's verification that `git ls-remote --tags origin` does **not** list the new tag. |
| `Bash(uv run scripts/promote_cli.py:*)` | A dry run of the installed promote script, which reports and pushes nothing. |

Two things this pre-approval set does **not** do. It does not make a promotion reachable from the
skill: the dry run is pre-approved, and the underlying push stays denied, so the only thing the skill
can invoke is the reporting half of that script. And it is a path-prefixed scope, so it matches
neither `scripts/promote_cli.py` run directly nor `uv run` given the script's absolute path — see
[A command scope matches text, not a program](../../../explanation/tool-grant-bounds.md#a-command-scope-matches-text-not-a-program).
Only the one spelling the body uses is declared.

Step 7b's `git ls-tree -r --name-only <tag>` is deliberately not pre-approved: it prompts, which
costs one approval on a step that is about to ask the builder questions anyway.

The `-r` is what keeps that cost at one. A `PUBLISH_PATHS` entry may be nested, so the builder has to
see paths below the first level to write one — and descending interactively would spend this approval
once per directory instead of once. A single recursive print buys every candidate path for the same
one prompt and needs no new grant, since the scope that would cover it (`Bash(git ls-tree:*)`) is not
declared in either direction.

**What this is not.** The denial is structural against the spellings an agent normally writes, and
against compound commands. It is **not** a boundary around `git` or `gh`, because a `Bash(...)` scope
matches command text rather than the program invoked. See
[A command scope matches text, not a program](../../../explanation/tool-grant-bounds.md#a-command-scope-matches-text-not-a-program)
for what evades it.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Where the installed scripts live

**The installed script's location is free.** `promote_cli.py` resolves the repository root itself with
`git rev-parse --show-toplevel`, reads `.promote-target` from that root, and prints the confirming
command for wherever it was invoked from — so a repository that wants it somewhere other than
`scripts/` may move it, and nothing in the base hardcodes the path. That matters for a repository
whose `scripts/` is itself published: anything left in a published directory publishes with it.

This repository installs both halves. Its copies of `release_cli.py`, the forge-release script, and
`promote_cli.py` live under `internal/scripts/` rather than `scripts/`, for that reason, and its
promote job runs only when started by hand.
