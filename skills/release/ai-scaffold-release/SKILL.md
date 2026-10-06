---
name: ai-scaffold-release
description: Configure a repository's release path — internally, version derivation from Conventional Commits, a git-cliff configuration, a release script, a forge-release script, CI jobs, and a local bootstrap tag; and on request a promote path that publishes one tag's filtered tree to a public target. Use when a repository has no release machinery yet, or when asked to set up releases, versioning, a changelog, or a public publish path.
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent, Bash(git push:*), Bash(git send-pack:*), Bash(gh:*), Bash(curl:*)"
allowed-tools: "Bash(uv --version:*), Bash(test:*), Bash(git remote:*), Bash(git tag:*), Bash(git log:*), Bash(git ls-remote:*), Bash(uv run scripts/promote_cli.py:*)"
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
through `scripts/promote_cli.py` or the job that runs it.

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

## 0. Check for `uv` — before anything else

Every script this skill runs or installs runs through `uv`, and a repository
that installs them needs `uv` and git and nothing else. Run `uv --version` first.

- **Not found:** stop. Say that `uv` is required and that it is installed from
  `https://docs.astral.sh/uv/`. Write nothing and route nothing, and fall back to
  nothing — no other interpreter, no other implementation of a script.
- **Found:** go on to step 1 without reporting the version, so the route
  decision is still the first thing said.

When a later `uv run` fails, say whose failure it is. `uv` fails **before the
script starts**, about Python or packages: no interpreter it may use, a download
that did not complete, a dependency it could not resolve. Show that error as it
is and stop — it is not a missing `uv`, so give no install link. Anything else
is the script's own output, such as one of its refusals: report it as the
script's, and do not mention installing `uv`.

## 1. Route — before the probe, and before any output

**First, refuse an installation made before the Python port.** If the repository
root holds any of `scripts/release.sh`, `scripts/gitlab-release.sh`,
`scripts/github-release.sh` or `scripts/promote.sh`, name each one present, say
that this version of the skill installs Python scripts run with `uv` and does not
write them beside bash ones, and stop. Write nothing, and neither delete nor
rewrite the bash scripts: migrating an existing install is not something this
skill does.

Otherwise, read `references/release-modes.md` and decide which install set you are writing:
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
   absent) → forge topology, reading the development-context block's forge,
   access, and exposure groups first, and no other key. See
   `references/forge-topologies.md`.
2. `git tag --list` → tag count, and whether the newest tag matches
   `v[0-9]+.[0-9]+.[0-9]+`.
3. Which of the five machinery files already exist at the repository root:
   `cliff.toml`, `scripts/release_cli.py`, the forge-release script, `Makefile`,
   the forge CI configuration.
4. `git log --format=%s` → the proportion of existing commit subjects the
   parser table in `references/commit-convention.md` would group, skip, or
   leave unmatched.

Print all four before asking anything. A builder who sees "3 commits, 0 tags,
0/3 subjects match a known type" is answering a different question than one
who sees "140 commits, 12 tags, 91% conventional."

## 3. Ask at most three questions

Never a fourth. Resolve every other choice from the probe or from a stated
default. (Step 7 asks its own questions, and this limit does not apply to them.)

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
2. `scripts/release_cli.py` (from `assets/release_cli.py`), executable
3. the forge-release script — `scripts/gitlab_release_cli.py` on GitLab (from
   `assets/gitlab_release_cli.py`), executable, and beside `release_cli.py`,
   whose GitLab step runs only when it finds this file there; none on GitHub,
   where the CI workflow itself creates the Release object
4. `Makefile` — add (or create, if absent) `release-preview` and `release`
   targets that delegate to `uv run scripts/release_cli.py`, never
   reimplementing its logic
5. the forge CI configuration — merge `assets/gitlab-ci-release.yml` into
   `.gitlab-ci.yml` on GitLab, or install `assets/github-release.yml` as
   `.github/workflows/release.yml` on GitHub

Then add `cliff.toml text eol=lf` and `scripts/*_cli.py text eol=lf` to
`.gitattributes`, creating it if absent, so a checkout on any platform keeps the
installed files, and the notes git-cliff renders from `cliff.toml`, free of `\r`.

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

A bootstrap tag is also unpublishable by construction: `assets/promote_cli.py`
refuses a tag that is not on origin, and this one never is.

## 7. The promote path — only when step 1 routed here

### 7a. Name the target, classify it, then pre-flight — before any file is written

Ask first **where the promotion publishes**. Offer **no default** and infer
nothing from an existing remote: a wrong value here is a push to somebody else's
repository. Then classify the target's forge from its host, with the first rule
of "Detecting the forge" in `references/forge-topologies.md`, state the
classification, and ask the builder to confirm it. A confirmed GitHub target gets
the Release step and the HTTPS-token job form; any other target gets neither.

Then report all three, perform none of them:

- **A push credential for the public target.** Absent is the normal case, and
  installation completes without one. A missing credential is not a failure of
  the install; it is the next thing the operator does. For a GitHub target, say
  that one fine-grained token with Contents: read and write authorizes both the
  push and the Release, that a deploy key cannot create a Release, and that the
  organisation may have to approve a fine-grained token before it works. For any
  other target, a deploy key with write access. On GitLab, also report the
  credential variable's **environment scope**: set it to `public`, the
  environment the installed `public:promote` declares, so no other job in the
  pipeline receives the credential. A variable left at the every-environment
  scope `*` still reaches the job, and every other job too.
- **Egress to the target host.** The SSH form needs port 22 reachable from
  wherever the promotion runs, the HTTPS-token form port 443. If it has never
  been measured, say *unmeasured* rather than assuming either answer, and name
  the one-job experiment that settles it.
- **Whether the public default branch is protected.** A protected branch
  refuses the lease push, and the refusal arrives after the confirmation was
  accepted.

The last two, and the credential, live in forge settings rather than in a
clone. **This skill cannot change a forge setting**, cannot create a
credential, and does not try; it reports each with the procedure and says
plainly which steps are the operator's.

### 7b. Print the tree, then ask what the probe cannot answer

Print the tag's tree first, in **one** recursive invocation —
`git ls-tree -r --name-only <tag>` — so the decision is made against the actual
list rather than from memory. Recursive because an allowlist entry may be
nested, and a nested entry has to be written against a path the builder can
see. One invocation because descending interactively would multiply a
permission prompt this step spends exactly once.

Then ask **which paths ship**. **Propose no allowlist.** It is an allowlist of
paths binding at every depth, so anything unnamed is withheld with no action
required, and a file's own name never withholds it. An entry may name a
directory or a single file, nested to any depth: naming `docs/guides` and
`docs/index.md` and not `docs` publishes `docs` **partially**, and every unnamed
sibling in it is withheld by the same absence. Say what that costs — a page
added there later does not ship until a line names it, and the dry run's
`withheld under <dir>:` block is where that is read. Do not name both a
directory and something inside it; the run refuses. Where help is wanted
deciding, run the configure-time audit from the repository root —
`uv run scripts/history_probe_cli.py <tag> <candidate-path>...`, with `scripts/`
in this skill's own directory — which reports, per withheld path, the earliest
commit at which it is still readable and the largest size it ever reached. That
audit is never written into the target repository. See
`references/mirror-scope.md`.

Ask every other question the probe and 7a left open — the target's forge, when
the builder did not confirm the classification, or the credential form the job
needs — and none whose answer the probe already determined.

### 7c. Write the files — four, or five for a GitHub target

1. `scripts/promote_cli.py` (from `assets/promote_cli.py`), executable
2. `.promote-target` (from `assets/promote-target.template`), with the target,
   the allowlist, and a neutral `PUBLISHER_IDENTITY` — one `PUBLISH_PATHS` line
   per path, values unquoted
3. the forge CI form — merge `assets/gitlab-ci-promote.yml` into
   `.gitlab-ci.yml` on GitLab, keeping exactly one credential form:
   `.promote-form-github` for a GitHub target, which carries the Release step's
   job line, or `.promote-form-ssh` for any other. Point `.promote-base`'s
   `extends:` at it and delete the other. Otherwise, the workflow form matching
   the topology step 2 probed, which carries no Release step
4. for a GitHub target only, `scripts/github_release_cli.py` (from
   `assets/github_release_cli.py`), executable
5. nothing else. **No `scripts/promote-gates.sh`, no gate directory, no
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
- promote: the files written, and that a run with **no** `CONFIRM_SHA` is a
  dry run reporting what would ship, while `CONFIRM_SHA=<tag object id> uv run
  scripts/promote_cli.py <tag>` performs it. The value is the `tag object:` id
  the dry run prints — not the commit id it also prints — so a tag moved or
  re-cut after the dry run refuses. `CONFIRM_SHA` is distinct from the internal
  path's confirmation and neither satisfies the other. For a GitHub target, the
  job then creates the Release. If that step fails after the push, re-running
  the promotion is refused, because the tag is already public; the recovery is
  `CONFIRM_SHA=<tag object id> PROMOTE_TOKEN=… uv run scripts/github_release_cli.py <tag>`,
  which is safe to re-run.

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

## 10. Offer to save the development context — after step 9

If this run detected or was told the forge, an access fact, or exposure, and
the development-context block lacks it, records it as stale, or records it as
`unresolved`, offer to save those facts. Read "Saving" in
`references/dev-context.md` first, even when step 2 found no block, and follow
it. A promote path installed by this run resolves
exposure as `public`, with its target. The rule step 9 gives holds here too:
with no question mechanism available, print the diff and write nothing. This
offer is not one of step 3's questions.
