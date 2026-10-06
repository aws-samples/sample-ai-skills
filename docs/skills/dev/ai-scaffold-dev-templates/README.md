---
title: "ai-scaffold-dev-templates"
sidebar_label: "ai-scaffold-dev-templates"
sidebar_position: 4
---

# `ai-scaffold-dev-templates`

| | |
|---|---|
| Invoke | `/ai-scaffold-dev-templates [--headless]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [dev](../) |
| Source | `skills/dev/ai-scaffold-dev-templates/SKILL.md` |
| Effort | `medium` |

## Overview

Writes a repository's forge collaboration files: a bug report and an enhancement issue template, a
pull or merge request template, and the review rules. Each file goes where its forge reads it, in
that forge's format. Every file is a bundled copy under the skill's `assets/`, so what the skill
writes can be read before it runs.

A missing file is created outright and reported afterwards. A change to a file that already exists,
to an agent-context file, or to `.promote-target` is shown as a diff and made only when the user
confirms it in a later turn. A second run on a repository holding the first run's output changes
nothing. The skill never commits, pushes, or calls a forge API.

## Arguments

| Argument | Effect |
|---|---|
| `--headless` | Ask nothing. Take the recommended option of every question, mark each such answer as inferred in the report, and apply no proposed diff. |

## The forge situation

Before writing anything, the skill decides which of three situations the repository is in:
*GitHub-primary*, *GitLab-primary*, or *GitLab-primary with a GitHub publish target*, where a
GitLab repository publishes a copy of itself to GitHub. It reads the answer from a
`<!-- ai-skills:dev-context -->` block in the root `AGENTS.md` or `CLAUDE.md` when one sets the
`forge` and `publish-target` keys. Otherwise it probes:

- `origin`'s host is `github.com`: GitHub.
- The host contains `gitlab`, or a root `.gitlab-ci.yml` exists: GitLab.
- Anything else: undetermined, and the skill asks.

A `PUBLIC_TARGET` on `github.com` in the root `.promote-target` is a GitHub publish target. The skill
shows what the probe found and asks the user to confirm it. With `--headless` it takes the probe's
conclusion, marks it as inferred, and writes nothing when the forge itself is undetermined.

## Where each file goes

| Template | GitHub | GitLab |
|---|---|---|
| Bug report | `.github/ISSUE_TEMPLATE/bug_report.yml` | `.gitlab/issue_templates/Bug.md` |
| Enhancement | `.github/ISSUE_TEMPLATE/enhancement.yml` | `.gitlab/issue_templates/Enhancement.md` |
| Issue chooser | `.github/ISSUE_TEMPLATE/config.yml` | — |
| Pull or merge request | `.github/pull_request_template.md` | `.gitlab/merge_request_templates/Default.md` |
| Review rules | `REVIEW.md` at the root | a `<!-- ai-skills:review-rules -->` block in the root `AGENTS.md` |

The GitHub issue templates are YAML issue forms, with `required: true` on each required field. The
GitLab templates are Markdown, with every instruction inside an HTML comment and each section's
comment beginning `Required.` or `Optional.`. Every field starts empty.

| Template | Required fields |
|---|---|
| Bug report | Title, Environment, Steps to reproduce, Observed behavior |
| Enhancement | Title, Problem, Proposed behavior |

Both forges require the title in their own title field, so the templates guide it rather than add a
section for it.

GitLab uses `.gitlab/merge_request_templates/Default.md` as the default merge request description
only when neither the project settings nor the parent group set a default template. Either of those
takes priority. On a GitLab version that does not apply `Default.md` automatically, the template
still appears in the template list.

### The review rules

The review rules list what counts as Important, and use only the three severity levels Claude Code
Review defines: Important, Nit, and Pre-existing. Style preferences are Nit at most.

On a GitHub-primary repository the rules go in `REVIEW.md` at the root, which Claude Code Review
reads. On a GitLab repository the skill writes no `REVIEW.md`, because nothing on GitLab reads it,
and a file that looks like review configuration but changes nothing is worse than no file. The same
rules go in a block in the root `AGENTS.md` instead, or in the root `CLAUDE.md` when there is no
`AGENTS.md` and `CLAUDE.md` is not a pointer to it. The report says that `REVIEW.md` was
deliberately not created.

### A repository that publishes to GitHub

In the *GitLab-primary with a GitHub publish target* situation, the skill writes both sets into the
GitLab repository: the GitLab set for its own use, and a GitHub set for the published copy. It asks
whether the public copy accepts issues and pull requests. The recommended answer is that it does
not, and then the GitHub set is a `config.yml` that turns blank issues off and a pull request
template saying pull requests are not accepted there. If it does accept them, the full GitHub set and
`REVIEW.md` are written.

It also proposes the `PUBLISH_PATHS=.github` line for `.promote-target`, plus `PUBLISH_PATHS=REVIEW.md`
when it writes `REVIEW.md`. Before writing any file of the published set, the skill checks it for
`origin`'s host and path, and refuses to write a file containing either. The refusal names the file
and the string.

GitHub reads issue forms and the pull request template only from the default branch, so the
published set takes effect once a publish updates the public repository's default branch.

## Template sources

The bug report is derived from The Good Docs Project's
[bug report template](https://gitlab.com/tgdp/templates/-/tree/v1.6.0/bug-report), tag `v1.6.0`,
under MIT No Attribution. Its required fields are that template's four non-optional sections. Good
Docs publishes no enhancement, pull request, or review template, so the others were written for this
skill. Every bundled file begins with a comment naming its source and license, and the skill keeps
that comment in every file it writes.

A static check keeps the GitHub and GitLab renderings of each template in step: the same sections, in
the same order, with the same required set.

## Output

Every run ends with one line per target (`created`, `matches`, `proposed`, `applied`, `refused`,
`skipped`), a count line, the forge situation and where it came from, and every answer taken as a
default. Nothing is committed, so review `git status` and `git diff` before committing.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Every template is bundled with the skill. |
| `Skill` | The skill invokes no other skill. Its report names one only as an optional hint. |
| `NotebookEdit` | It writes templates, `REVIEW.md`, an agent-context block, and `.promote-target` lines, and no notebook. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(git remote get-url:*), Bash(git rev-parse:*), Bash(test:*), Bash(cmp:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git remote get-url:*)` | Step 1, reading `origin`'s host and path. |
| `Bash(git rev-parse:*)` | Resolving the repository root. |
| `Bash(test:*)` | Step 2, checking whether each target exists. |
| `Bash(cmp:*)` | Steps 2, 4 and 6, comparing a target with its bundled copy byte for byte. |

All four commands only read. None of them changes a file.

**`mkdir` and `cp` are deliberately not pre-approved**, although Step 4 copies every bundled file
with them. Leaving them unapproved means each copy prompts, so a person sees every file the skill is
about to write. Edits to agent-context files and `.promote-target` go through the Edit tool, which
prompts the same way.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).

## Pages

No page is specific to this skill yet — its behaviour is defined by its `SKILL.md`.
