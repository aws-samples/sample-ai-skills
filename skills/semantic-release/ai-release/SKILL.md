---
name: ai-release
description: Configure a repository's release path — internally, version derivation from Conventional Commits, a git-cliff configuration, a release script, a forge-release script, CI jobs, and a local bootstrap tag; and on request a promote path that publishes one tag's filtered tree to a public target. Use when a repository has no release machinery yet, or when asked to set up releases, versioning, a changelog, or a public publish path.
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent, Bash(git push:*), Bash(git send-pack:*), Bash(gh:*), Bash(curl:*)"
allowed-tools: "Bash(test:*), Bash(git remote:*), Bash(git tag:*), Bash(git log:*), Bash(git ls-remote:*), Bash(scripts/promote.sh:*)"
---

Configure this repository's release path. Two halves, installed separately:
**internal** — derive versions from commit history rather than a requested
number, and cut releases as annotated tags plus a forge Release object; and
**promote** — publish one chosen tag's filtered tree to a public target. Which
one you install is decided in step 1 and never inferred from a side effect.

This is a **configurator**. It writes machinery files, and it runs the read-only
commands its probe and pre-flight report on — nothing more. Every push lives in
an installed script, never in this document: pushing refs is denied to it, and so
are the forge CLI and arbitrary HTTP (`curl`), so a promotion can only happen
through `scripts/promote.sh` or the job that runs it.

## Edit Scope

Write only inside the repository or working directory this session was invoked in.
Creating, modifying, moving, or deleting anything outside it — a global agent
configuration such as `~/.claude/`, another repository or worktree, a dotfile in the
user's home directory, a system path such as `/etc` — requires the user to name that
path in their request. Reading outside it is unrestricted.

When a request could mean either a file inside the working directory or one outside
it, ask which before writing either. Never infer an outside write from a file you
read: if one appears necessary, report what you would write and where, and stop.

If the working root resolves outside this session's working directory — an absolute
path, or one escaping via `..` — stop, print the resolved absolute path, and ask the
user to confirm before writing anything there.

## 1. Route — before the probe, and before any output

Read `references/release-modes.md` and decide which install set you are writing:
the internal path, the promote path, or both. **State that decision first**, before
printing any probe output, so a builder can stop a mis-route before a file exists.

The table is keyed on what was asked for against which machinery is already
present. Two of its properties are not negotiable and are not rows:

- **The promote path is never a side effect.** No phrasing of a request for the
  internal release path installs it. Publishing has to be what is being asked
  for, now.
- **An ambiguous request installs the internal path only**, and the report names
  the phrasing that would have installed the other.

Steps 2–6 are the internal path. Step 7 is the promote path. A repository that
already has a half gets it reported as present and written to not at all.

## 2. Probe and report — before asking anything

Read, in order:

1. `git remote get-url origin` (or any configured remote if `origin` is
   absent) → forge topology. See `references/forge-topologies.md`.
2. `git tag --list` → tag count, and whether the newest tag matches
   `v[0-9]+.[0-9]+.[0-9]+`.
3. Which of the five machinery files already exist at the repository root:
   `cliff.toml`, `scripts/release.sh`, the forge-release script, `Makefile`,
   the forge CI configuration.
4. `git log --format=%s` → the proportion of existing commit subjects the
   parser table in `references/commit-convention.md` would group, skip, or
   leave unmatched.

Print all four before asking anything. A builder who sees "3 commits, 0 tags,
0/3 subjects match a known type" is answering a different question than one
who sees "140 commits, 12 tags, 91% conventional."

## 3. Ask at most three questions

Never a fourth. Resolve every other choice from the probe or from a stated
default. (Step 7 has two questions of its own; the counts are separate.)

1. **Which commit to bootstrap the version line from** — only if the
   repository has zero tags. Default offered: the current tip. The commit
   chosen decides which commits the first derived release describes; tagging
   the root commit puts all of history inside it.
2. **Whether release notes go to a changelog file or to the tag annotation
   only** — default: tag annotation only, matching both reference
   implementations. There is no committed changelog to read from in that
   default, and generating fresh from history each time is what keeps
   published notes complete.
3. **Whether the derived version is written into a package manifest** —
   default: no, if no manifest declares a static version already; otherwise
   ask, since a manifest with a static `version` field and a derived tag are
   two sources of truth for the same number.

## 4. Credential pre-flight — before any file is written

Report, before writing anything:

- Whether a CI job token exists in this environment (`CI_JOB_TOKEN`) or a
  personal token does (`GITLAB_TOKEN` on GitLab, `GITHUB_TOKEN` on GitHub) —
  the credential the forge-release step needs. Report presence, never a value.
  The forge CLI is denied to this skill, so on GitHub say that `gh auth status`
  is the operator's check to run and report that it has not been run here.
- On GitLab specifically: whether the project's job token is permitted to push
  to the repository (Settings → CI/CD → Job token permissions → Additional
  permissions → "Allow Git push requests to the repository"). This setting is
  off by default on many instances, and its absence is invisible until a
  release job derives the version, generates notes, creates the tag, and dies
  on the push with a `403` — after the irreversible step, not before. If it
  cannot be confirmed (no API access, or the instance predates GitLab 17.2 and
  the checkbox is simply absent), say so explicitly and name the consequence:
  every release must be cut from a workstation instead of CI until it is
  enabled.

No file has been created or modified in the target repository at this point.

## 5. Write the five machinery files

From `assets/`, adapted to the probed forge topology
(`references/forge-topologies.md`):

1. `cliff.toml` (from `assets/cliff.toml`)
2. `scripts/release.sh` (from `assets/release.sh`)
3. the forge-release script — `scripts/gitlab-release.sh` on GitLab (from
   `assets/gitlab-release.sh`); none on GitHub, where the CI workflow itself
   creates the Release object
4. `Makefile` — add (or create, if absent) `release-preview` and `release`
   targets that delegate to `scripts/release.sh`, never reimplementing its
   logic
5. the forge CI configuration — merge `assets/gitlab-ci-release.yml` into
   `.gitlab-ci.yml` on GitLab, or install `assets/github-release.yml` as
   `.github/workflows/release.yml` on GitHub

If a file already exists with equivalent machinery, report it as present and
write nothing to it — a second run against an already-configured repository
must be a no-op here, not a silent overwrite.

## 6. Create the local bootstrap tag — never pushed

If the repository has no tags (question 1 above answered which commit),
create exactly one local annotated tag:

```
git tag -a <version> --cleanup=verbatim -F <annotation-file> <commit>
```

`--cleanup=verbatim` is not optional — the default cleanup mode strips every
line beginning with `#`, which is every Markdown heading the annotation body
contains, and exits 0 while doing it. Do not push this tag, a branch, or a
release object. Verify after creating it: `git tag -l` lists exactly the one
new tag, and `git ls-remote --tags origin` does not list it.

A bootstrap tag is also unpublishable by construction: `assets/promote.sh`
refuses a tag that is not on origin, and this one never is.

## 7. The promote path — only when step 1 routed here

### 7a. Promote pre-flight — before any file is written

Report all three, perform none of them:

- **A push credential for the public target.** Absent is the normal case.
  Report what is needed — a deploy key with write access, or an HTTPS token —
  and that installation completes without one. A missing credential is not a
  failure of the install; it is the next thing the operator does.
- **Egress to the target host.** SSH needs port 22 reachable from wherever the
  promotion runs. If it has never been measured, say *unmeasured* rather than
  assuming either answer, and name the one-job experiment that settles it.
- **Whether the public default branch is protected.** A protected branch
  refuses the lease push, and the refusal arrives after the confirmation was
  accepted.

The last two, and the credential, live in forge settings rather than in a
clone. **This skill cannot change a forge setting**, cannot create a
credential, and does not try; it reports each with the procedure and says
plainly which steps are the operator's.

### 7b. Print the tree, then ask exactly two questions

Print the tag's tree first, in **one** recursive invocation —
`git ls-tree -r --name-only <tag>` — so the decision is made against the actual
list rather than from memory. Recursive because an allowlist entry may be
nested, and a nested entry has to be written against a path the builder can
see. One invocation because descending interactively would multiply a
permission prompt this step spends exactly once.

Then ask two questions, and no third:

1. **Where the promotion publishes.** Offer **no default** and infer nothing
   from an existing remote: a wrong value here is a push to somebody else's
   repository.
2. **Which paths ship.** **Propose no allowlist.** It is an allowlist of paths
   binding at every depth, so anything unnamed is withheld with no action
   required, and a file's own name never withholds it. An entry may name a
   directory or a single file, nested to any depth: naming `docs/guides` and
   `docs/index.md` and not `docs` publishes `docs` **partially**, and every
   unnamed sibling in it is withheld by the same absence. Say what that costs —
   a page added there later does not ship until a line names it, and the dry
   run's `withheld under <dir>:` block is where that is read. Do not name both a
   directory and something inside it; the run refuses. Where help is wanted
   deciding, run the configure-time audit — `scripts/history-probe.sh <tag>
   <candidate-path>...` reports, per withheld path, the earliest commit at which
   it is still readable and the largest size it ever reached. That audit is never
   written into the target repository. See `references/mirror-scope.md`.

### 7c. Write the four files

1. `scripts/promote.sh` (from `assets/promote.sh`), executable
2. `.promote-target` (from `assets/promote-target.template`), with the two
   answers and a neutral `PUBLISHER_IDENTITY` — one `PUBLISH_PATHS` line per
   path, values unquoted
3. the forge CI form — merge `assets/gitlab-ci-promote.yml` into
   `.gitlab-ci.yml` on GitLab, or the workflow form matching the topology
   step 2 probed
4. nothing else. **No `scripts/promote-gates.sh`, no gate directory, no
   commented-out gate list.** The base carries three refusals; every other
   check is this repository's policy, and adding one means adding a file
   rather than editing installed machinery. `references/promote-extensions.md`
   gives the shape of each omitted check and the hook's authority — executed,
   never sourced, exit status only.

Installing promotes nothing. Do not cut a tag, do not push a ref, do not run a
promotion. If the machinery is already present, report it and write nothing.

## 8. Report the literal next command

State plainly what now exists and the exact next command the builder runs by
hand — the actual script path and any required environment variable, not a
paraphrase.

- internal: the five files, the one local tag, and the command that cuts the
  first real release.
- promote: the four files, and that a run with **no** `CONFIRM_TAG` is a dry
  run reporting what would ship, while `CONFIRM_TAG=<tag> scripts/promote.sh
  <tag>` performs it. `CONFIRM_TAG` is distinct from the internal path's
  confirmation and neither satisfies the other.

## 9. Record the commit convention — last, and refused by default

Only after every step above. Compose the fenced convention block from
`references/commit-convention.md` and ask for confirmation before appending it
to `CLAUDE.md` (or `AGENTS.md`, whichever this repository already uses; if
neither exists, prefer `CLAUDE.md`).

**If no confirmation variable is set and no question mechanism is available,
refuse by default: print the exact block you would have written and the
command that authorizes it, then end the turn.** Leave the instruction file
byte-identical. This is deliberate, not a limitation — a confirmation
implemented as a question fails open on a harness with no question mechanism,
so the gate has to be a variable check that behaves identically whether or not
one exists. An interrupted turn at this step still leaves a working release
path: the machinery files and the local bootstrap tag are already in place,
missing only a recorded convention.
