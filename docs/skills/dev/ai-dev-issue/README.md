---
title: "ai-dev-issue"
sidebar_label: "ai-dev-issue"
sidebar_position: 2
---

# `ai-dev-issue`

| | |
|---|---|
| Invoke | `/ai-dev-issue [description] [--dry-run] [--local] [--tracker <name>] [--no-investigate] [--one]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [dev](../) |
| Source | `skills/dev/ai-dev-issue/SKILL.md` |
| Effort | `high` |

## Overview

File a clear, complete issue in whatever tracker the project uses — GitHub, GitLab, Asana, Jira — or a
dated markdown file when there is none. Investigates the root cause first, respects the project's issue
templates, types, and labels, and infers defect vs enhancement.

## Arguments

| Argument | Effect |
|---|---|
| a description | The problem or the thing to build. With none, the skill uses the problem just discussed in the session. |
| `--dry-run` | Draft the issue and print it. Nothing is created. |
| `--local` | Write the dated markdown file even when a tracker exists. |
| `--tracker <name>` | Override detection: `github`, `gitlab`, `asana`, `jira`, or `local`. |
| `--no-investigate` | Skip the investigation phase and file from what is already known. |
| `--one` | File one issue even when the input names several problems. |
| `--headless` | Ask nothing. Take every recommended answer, and save no development context. Stop rather than send a credential to a host nobody chose; see [Credentials and trust](#credentials-and-trust). |

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`forge`, `web_host`, `ssh_host`, `project`, `project_id`, `cli`, `exposure`, `public_target`, and `tracker`. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. With
`--headless`, it saves nothing, and when `origin` names a forge it cannot identify it stops and
creates no issue.
[`ai-scaffold-dev-context`](../ai-scaffold-dev-context/) records every key at once.

## Credentials and trust

When the tracker is GitHub or GitLab, the skill sends your forge credential on every tracker call it
makes: checking that issues are enabled, reading labels and recent issues, searching for duplicates,
creating the issue. On GitHub that is the token `gh` holds, or `GITHUB_TOKEN` when `gh` is absent. On
GitLab it is `GITLAB_TOKEN`, plus an SSO session cookie on an instance behind a sign-on gate. They go
out through `gh`, `glab`, or `curl`. An Asana or Jira tracker is reached through an MCP server, which
holds its own credential; the skill sends none.

**Repository content can propose where they go.** A repository's `CLAUDE.md` or `AGENTS.md` can
carry an auth recipe naming an API host. Its development-context block can record a `web_host`.
Anyone who can commit to the repository can write either. So the skill sends a credential without
asking only to a host derived from `origin`, or to one you set:

- **Derived from `origin`:** the host of an HTTPS `origin`; `github.com` or `gitlab.com`; or `<rest>`
  for an SSH host `ssh.<rest>`, such as `git.example.internal` for `ssh.git.example.internal`.
- **Set by you:** `GITLAB_HOST` or `GH_HOST` in the environment when the run starts, or a host you
  typed during the run.

For any other host it asks first. The question names the host, the credential, the `origin` URL,
and where the host came from, and its recommended answer is not to send. A repository's auth recipe
still decides *how* to authenticate (the CLI, headers, and cookie handling), but not *where*. The
rule is `references/forge-credentials.md` in the skill.

**With `--headless`, the skill stops instead of asking.** It sends nothing to that host, creates no
issue, and names the host and its source. To run headless against a GitLab whose web host `origin`
does not give, export `GITLAB_HOST` first. `--headless` removes only the skill's own questions. It
does not remove the harness's permission prompt.

**Run it only against repositories you trust, or set the host yourself** by exporting `GITLAB_HOST`
or `GH_HOST` before the run.

**The skill also reads text other people write.** Its investigation reads repository content —
source files and their comments, logs, test output, issue templates — and its duplicate search
reads existing issues. Anyone who can commit to the repository or file an issue can write any of
these. The skill then posts to your tracker with your credentials. It treats that text as evidence:
only your description instructs it. A directive addressed to an agent — file somewhere else, add a
label, comment on another issue, send a file — is reported under **Directives found** and left out
of the issue, even when it sits in a log or code excerpt the issue would otherwise quote. Treating
that text as evidence is an instruction to the model, not an enforced boundary: a model that does
not follow the instruction acts on the directive.

Two controls stand between your credential and a host or a directive that someone else planted:

- **The skill's own rules: the host question or the headless stop, and treating read text as
  evidence.** They work only if the agent follows the skill's instructions.
- **The harness's permission prompt.** It shows each command, including the host it sends to, before
  the command runs, and it works whether or not the agent follows the skill. Pre-approving `curl`,
  `gh`, or `glab` in your settings, or running with permission prompts bypassed, removes it. The
  skill never asks you to do either.
  [Recommended consumer-side settings](../../../explanation/tool-grant-bounds.md#recommended-consumer-side-settings)
  shows how to deny those commands instead.

## Tool grants

**Denial set** — `WebSearch, NotebookEdit, Agent, Skill`

| Entry | Reason |
|---|---|
| `WebSearch` | Phase 2 investigates the repository — code, logs, failing tests — and its duplicate search queries the tracker, not the web. |
| `NotebookEdit` | No step names a notebook. The one file the skill writes into the project is Phase 6's `YYYY-MM-DD-<slug>-issue.md`. |
| `Agent` | No fan-out step. Phase 2 bounds the investigation itself, at two or three passes. |
| `Skill` | Phase 6 *mentions* `/ai-dev-autopr <path>` as the next step; it invokes nothing. |

`WebFetch` is not denied. No step names it.

**Pre-approval set** — none. This skill declares no `allowed-tools` key, so every command it runs
prompts unless the consumer's own settings approve it. The body creates the issue with no approval
gate of its own, and other people are notified the moment it posts, so the permission prompt on the
create call is the only point at which a person sees that call before it runs.
[Credentials and trust](#credentials-and-trust) says what removes that prompt.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
