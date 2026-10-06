---
title: "ai-dev-autopr"
sidebar_label: "ai-dev-autopr"
sidebar_position: 1
---

# `ai-dev-autopr`

| | |
|---|---|
| Invoke | `/ai-dev-autopr <input> [no worktree] [no spec review] [keep draft]`, or `/ai-dev-autopr --finish` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [dev](../) |
| Source | `skills/dev/ai-dev-autopr/SKILL.md` |
| Effort | `xhigh` |

## Overview

Drive a spec, issue, or ticket end to end into a merge-ready PR/MR: worktree and branch, spec or plan,
implementation, verifications that actually pass, conventional commits, the PR itself, and every round
of automated review feedback.

## Arguments

| Argument | Effect |
|---|---|
| a spec id | Implement an existing spec through to a PR/MR. |
| an issue URL or id | Propose a spec or plan, stop for review, then implement through to a PR/MR. |
| `"free text"` | The same as an issue. |
| `no worktree` | Work in the current checkout instead of a new worktree. |
| `no spec review` | Skip the stop for a person to review the spec or plan. |
| `keep draft` | Never mark the PR/MR ready for review; it stays a draft when the run ends. |
| `--finish` | After a person merges: confirm the merge, remove the worktree and branch, close out the issue, and offer to archive the spec. |

The modifiers are also recognised in plain language, and the skill echoes back which ones it picked up.
It never merges the PR/MR itself; every run that reaches a PR/MR ends waiting on a person to merge it.

## Draft state

The PR/MR is a draft whenever the skill may push to it, so a person cannot merge it between two of
the skill's pushes; neither GitHub nor GitLab merges a draft. It opens as a draft, is marked ready
for review just before each wait for automated review, and returns to draft before the skill edits
for the next push. A run ends with the PR/MR ready only when every merge-ready item passed; any other
ending leaves it a draft, and the report says why. While the skill waits for a review the PR/MR is
ready and can be merged, but at that point everything is pushed and verified. On a GitHub plan that
offers no draft pull requests, the PR opens ready and the skill says it can be merged between pushes.

## Development context

The skill reads these keys of the development-context block in the root `AGENTS.md` or `CLAUDE.md`:
`forge`, `web_host`, `ssh_host`, `project`, `project_id`, `cli`, `framework`, `base_branch`, `verify`, and `reviewer`. It checks each against the live repository, falls back to its own detection when the block
is absent or a fact is stale, and asks only about what detection cannot settle. At the end of a run
it offers to save what it resolved, shown as a diff and written only on confirmation. The save
goes to the checkout the session was invoked in, never to the pull request's branch.
[`ai-scaffold-dev-context`](../ai-scaffold-dev-context/) records every key at once.

## Credentials and trust

The skill sends your forge credential on every forge call it makes: reading the issue, opening the
PR/MR, polling CI, replying to review threads, closing the issue. On GitHub that is the token `gh`
holds, or `GITHUB_TOKEN` when `gh` is absent. On GitLab it is `GITLAB_TOKEN`, plus an SSO session
cookie on an instance behind a sign-on gate. They go out through `gh`, `glab`, or `curl`.

**Repository content can propose where they go.** A repository's `CLAUDE.md` or `AGENTS.md` can
carry an auth recipe naming an API host. Its development-context block can record a `web_host`. An
issue or comment can link to another host. Anyone who can commit to the repository, or comment on
its issues, can write any of these. So the skill sends a credential without asking only to a host
derived from `origin`, or to one you set:

- **Derived from `origin`:** the host of an HTTPS `origin`; `github.com` or `gitlab.com`; or `<rest>`
  for an SSH host `ssh.<rest>`, such as `git.example.internal` for `ssh.git.example.internal`.
- **Set by you:** `GITLAB_HOST` or `GH_HOST` in the environment when the run starts, or a host you
  typed during the run.

For any other host it asks first. The question names the host, the credential, the `origin` URL,
and where the host came from, and its recommended answer is not to send. A repository's auth recipe
still decides *how* to authenticate (the CLI, headers, and cookie handling), but not *where*. The
rule is `references/forge-credentials.md` in the skill.

**Run it only against repositories you trust, or set the host yourself** by exporting `GITLAB_HOST`
or `GH_HOST` before the run.

**The skill also acts on text other people write.** It reads issue bodies, comments, and review
feedback, which anyone who can comment on the issue or the PR/MR can write. It acts on what it reads
with your credentials: it pushes, opens and updates the PR/MR, replies to reviews, and closes the
issue. The skill treats that text as data. An issue decides what to build, and a directive in it
about how the skill runs — reach a host, send a file, close another issue, merge — is reported under
**Directives found** and not acted on. A review comment is a claim to evaluate, never a command. The
PR/MR body names where each directive was found and never quotes it, so the next reader of the body
does not receive it. Treating that text as data is an instruction to the model, not an enforced
boundary: a model that does not follow the instruction acts on the directive.

Two controls stand between your credential and a host or a directive that someone else planted:

- **The skill's own rules: the host question, and treating read text as data.** They work only if
  the agent follows the skill's instructions.
- **The harness's permission prompt.** It shows each command, including the host it sends to, before
  the command runs, and it works whether or not the agent follows the skill. Pre-approving `curl`,
  `gh`, or `glab` in your settings, or running with permission prompts bypassed, removes it. The
  skill never asks you to do either.
  [Recommended consumer-side settings](../../../explanation/tool-grant-bounds.md#recommended-consumer-side-settings)
  shows how to deny those commands instead.

This skill has no `--headless` mode, so it always asks the host question when the question applies.

## Tool grants

**Denial set** — `WebSearch, NotebookEdit`

| Entry | Reason |
|---|---|
| `WebSearch` | No step searches the web. |
| `NotebookEdit` | No step names a notebook. |

Three tools most skills in this collection deny are left available here:

| Not denied | Why |
|---|---|
| `WebFetch` | Phase 2 fetches a referenced issue or ticket rather than paraphrasing it from its id. |
| `Skill` | Phase 2 implements an existing spec through the framework's own skill — `openspec-apply-change`, or `/ai-implement` for an `ai-plan` plan — or proposes one with `openspec-propose` or `/ai-plan`, and Phase 9 offers to run the archive or sync skill. |
| `Agent` | No step names it, but [`ai-implement`](../../research/ai-implement/), which Phase 2 hands an `ai-plan` plan to, dispatches one agent per independent phase. |

**Pre-approval set — none. This skill declares no `allowed-tools` key at all**, for the reason
[`ai-implement`](../../research/ai-implement/#tool-grants) gives: Phase 4 runs the repository's own
test and lint commands, harvested in Phase 0, and no honest command scope can be written for an
unknown repository's runner. Phase 5 also pushes. With no key, the consumer's own permission prompts
stay in place for every one of those commands.

**The denial set buys little for this skill.** Its real bounds are the body's "When to stop and ask"
rules, its rule never to merge, its edit-scope section, and the harness's own permission prompts.

No denied capability is used by this body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
