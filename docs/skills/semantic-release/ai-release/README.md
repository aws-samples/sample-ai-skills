---
title: "ai-release"
sidebar_label: "ai-release"
sidebar_position: 4
---

# `ai-release`

| | |
|---|---|
| Invoke | `/ai-release` |
| Activation | slash command, or when a request matches the skill description |
| Domain | [semantic-release](../) |
| Source | `skills/semantic-release/ai-release/SKILL.md` |

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
| `scripts/release.sh` | `assets/release.sh` |
| `scripts/gitlab-release.sh` (GitLab only) | `assets/gitlab-release.sh` |
| `Makefile` targets `release-preview`, `release` | delegate to `scripts/release.sh` |
| CI job or workflow | `assets/gitlab-ci-release.yml` / `assets/github-release.yml` |
| one local annotated bootstrap tag, never pushed | — |

## The promote half

| Writes | From |
|---|---|
| `scripts/promote.sh` | `assets/promote.sh` |
| `.promote-target` | `assets/promote-target.template` |
| CI job or workflow | `assets/gitlab-ci-promote.yml` |

`.promote-target` carries three keys — `PUBLIC_TARGET`, `PUBLISH_PATHS` (one line per path),
`PUBLISHER_IDENTITY` — and is **parsed as `key=value`, never sourced**, so nothing in it can
authorize a push. The confirmation is read from the environment only.

**Three refusals**, all of them before the temporary worktree exists:

1. the configuration is absent;
2. `CONFIRM_TAG` does not equal the tag being promoted;
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
silently not shipping — otherwise hides. `scripts/history-probe.sh` is an optional configure-time
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

The script is invoked by its own path — `scripts/promote.sh` as installed, wherever the repository
moved it otherwise:

```
<promote.sh> [TAG]                      # dry run — reports, pushes nothing
CONFIRM_TAG=v0.4.0 <promote.sh> v0.4.0  # promotes
```

There is no `--dry-run` flag: omitting `CONFIRM_TAG` is what makes a run a dry run. `CONFIRM_TAG` is
distinct from the internal path's confirmation and neither satisfies the other. Every dry run prints
the tag, the target, the paths that ship, the paths withheld, whether a repository gate hook is
present, and the exact confirmation to re-run with.

## Tool grants

- **Denied:** `WebFetch`, `WebSearch`, `Skill`, `NotebookEdit`, `Agent`, `Bash(git push:*)`, `Bash(git send-pack:*)`, `Bash(gh:*)`, `Bash(curl:*)`
- **Pre-approved:** `Bash(test:*)`, `Bash(git remote:*)`, `Bash(git tag:*)`, `Bash(git log:*)`, `Bash(git ls-remote:*)`, `Bash(scripts/promote.sh:*)`

Every entry's reason, and what these declarations do **not** bound, is in
[Tool Grants](../tool-grants.md).

## This repository does not use the promote half

The skill bundles `assets/promote.sh` and ships the capability. Installing it writes a
`.promote-target`, a copy of `promote.sh`, and one manual CI job; installing it promotes nothing, and
a promotion additionally needs a push credential that the skill cannot create.

**The installed script's location is free.** `promote.sh` resolves the repository root itself with
`git rev-parse --show-toplevel`, reads `.promote-target` from that root, and prints the confirming
command for wherever it was invoked from — so a repository that wants it somewhere other than
`scripts/` may move it, and nothing in the base hardcodes the path. That matters for a repository
whose `scripts/` is itself published: anything left in a published directory publishes with it.
