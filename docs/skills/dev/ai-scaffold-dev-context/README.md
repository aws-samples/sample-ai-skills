---
title: "ai-scaffold-dev-context"
sidebar_label: "ai-scaffold-dev-context"
sidebar_position: 3
---

# `ai-scaffold-dev-context`

| | |
|---|---|
| Invoke | `/ai-scaffold-dev-context [--headless]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [dev](../) |
| Source | `skills/dev/ai-scaffold-dev-context/SKILL.md` |
| Effort | `high` |

## Overview

An agent that guesses a repository's forge, its spec framework, or the host its forge's API answers on
opens a pull request in the wrong shape or sends requests to the wrong place. This skill settles eight
facts about how a repository is developed and records them as one block in the root `AGENTS.md`. Every
agent session reads that file, so the facts are in context with no further detection.

Run it once in each repository you work in, and again when one of the facts changes. Skills that use
these facts work without the block too: they detect what they need, and ask about what they cannot
detect.

## Arguments

| Argument | Effect |
|---|---|
| none | Resolve every fact, ask about the rest, show the diff, and write it on confirmation. |
| `--headless` | Ask nothing. Take the recommended answer to every question, mark each such answer as inferred, print the diff, and write nothing. |

## The eight facts

| Fact | Keys in the block | Where it comes from |
|---|---|---|
| Forge | `forge` | The `origin` host, then a root `.gitlab-ci.yml`, which identifies a self-managed GitLab whose host name does not contain `gitlab`. |
| Access | `web_host`, `ssh_host`, `project`, `project_id`, `cli` | The `origin` URL. The web and API host is resolved separately from the SSH host: for `git@ssh.git.example.internal:group/project.git` the skill asks for it and recommends `git.example.internal`. |
| Exposure | `exposure`, `public_target` | `.promote-target`, the CI configuration, and the project's visibility on the forge. |
| Spec framework | `framework` | `openspec/`, `.specify/`, or `.kiro/specs/`. |
| Base branch | `base_branch` | `refs/remotes/origin/HEAD`, then the forge's default branch. |
| Verification | `verify` | `Makefile` targets, `package.json` scripts, the test runner `pyproject.toml` configures, and the CI jobs. Always confirmed with you, even when detected. |
| Issue tracker | `tracker` | A tracker the agent-context files declare, then the forge's own issues. |
| Automated reviewer | `reviewer` | A review job in CI, a reviewer the agent-context files name, or a bot's review on a recent merged pull or merge request. |

Evidence in the filesystem and git outranks prose. The skill reads the agent-context files only to find
a statement that disagrees with that evidence — `AGENTS.md` saying no publish path exists while
`.promote-target` names one, for example — and for the forge CLI, the tracker, and the reviewer, which no
file settles. It reports each disagreement with the file and line of both sides and asks which applies.

Exposure ends in one of four outcomes: a publish path configured and run by a CI job; a publish path
configured but run by no job; no publish path; or cannot determine, when the CI configuration includes
a file from another project. A repository whose exposure cannot be determined is treated as public until
you answer.

## Questions

The skill asks only about a fact no signal reaches, or one two signals disagree on. It asks in rounds of
one to four questions, each with a recommended answer, and records anything you leave unanswered as
`unresolved` rather than as a guess.

## The block

```markdown
<!-- ai-skills:dev-context -->
## Development context

Facts about how this repository is developed, for agents. Correct a wrong line by editing it.

- forge: gitlab
- web_host: git.example.internal
- ssh_host: ssh.git.example.internal
- project: group/project
- project_id: 1234
- cli: glab
- exposure: internal
- public_target: none
- framework: openspec
- base_branch: main
- verify: `make test`; `make lint`
- tracker: forge
- reviewer: none
- recorded: 2026-01-15
<!-- /ai-skills:dev-context -->
```

The block goes in the root `AGENTS.md` when it exists, otherwise in the root `CLAUDE.md`, otherwise in a
new root `AGENTS.md`, and never in more than one file. The skill shows the change as a diff and writes it
only when you confirm. A later run replaces the text between the markers, so the diff shows only the
lines that changed.

When the file holding the block is itself published — a `.promote-target` `PUBLISH_PATHS` entry covers
it, or the project is publicly visible — the skill still records the forge, but writes the hosts, the
project path, and the project id as `withheld`.

## Output

The report gives one line per key with its value and the signal behind it, then every disagreement and
how it was settled, every withheld line, every forge read that failed, and every answer taken as a
default. The skill also checks this machine: whether the forge CLI is installed, and whether it is
authenticated to the recorded host. It reports each gap with the command that closes it, and records
nothing about the machine in the block. It commits nothing.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent, Bash(git push:*)`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches a page. Forge facts come from the forge CLI. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | The only file it writes is the root agent-context file. |
| `Agent` | No step fans out. |
| `Bash(git push:*)` | The skill commits nothing and pushes nothing. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(git remote get-url:*), Bash(git ls-files:*), Bash(test:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(git remote get-url:*)` | Step 2, reading the `origin` URL that decides the forge and the access facts. |
| `Bash(git ls-files:*)` | Step 2, listing the CI configuration and framework files. |
| `Bash(test:*)` | Steps 1 and 2, checking with `test -e` and `test -f` which files exist. |

All four commands only read. `git remote` is pre-approved only for `get-url`, because its other
subcommands add, rename, and remove remotes. Forge reads through `gh` and `glab` are not pre-approved, so
each one prompts.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
