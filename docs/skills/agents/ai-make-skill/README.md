---
title: "ai-make-skill"
sidebar_label: "ai-make-skill"
sidebar_position: 3
---

# `ai-make-skill`

| | |
|---|---|
| Invoke | `/ai-make-skill [description]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [agents](../) |
| Source | `skills/agents/ai-make-skill/SKILL.md` |
| Effort | `high` |

## Overview

The skill writes one new skill as an [Agent Skills](https://agentskills.io) folder: a `SKILL.md`, plus
the `references/`, `scripts/`, and `assets/` subdirectories the request needs. The written skill follows
the standard by default, so a skill written for no agent in particular is valid under the standard
alone. A frontmatter key or a file that only one agent reads is added only for an agent the user has
confirmed, and is labelled with that agent in the frontmatter.

The skill holds one table about agents: each agent's name, the environment variable that identifies it,
and its configuration directory. It uses the table only to suggest which agent is meant. Every fact
that shapes the written folder — the frontmatter keys an agent reads, how a skill is invoked under it,
any file it needs beside `SKILL.md`, and the directory it reads skills from — comes from the user. When
the user does not know one of those facts, the skill writes the standard form for that part and reports
the gap rather than looking the fact up.

## Input

| Input | What it selects |
|---|---|
| a description of the skill | Every choice the description answers is taken from it; the rest is asked. |
| a request to turn work in the conversation into a skill | The steps, tools, corrections, and input and output forms are taken from the conversation; the rest is asked. |
| nothing | The skill asks what the new skill should do before doing anything else. |

## What it does

1. **Detects the agent, then confirms it.** It checks the environment variables in its table, then the
   configuration directories at the repository root, and reports what each step found. It always asks
   which agent the new skill is for, even when it found exactly one, because the agent running the
   skill is not necessarily the agent the new skill is for. With two candidates it lists both and picks
   neither. With none it offers the standard with no agent-specific additions as an answer.
2. **Asks only what the request leaves open**, in one batch, each question stating the default that
   applies if it goes unanswered: name, description, activation, the input the new skill takes, an
   editing boundary, optional standard fields, each confirmed agent's facts, bundled scripts, and a
   `references/` split.
3. **Confirms a summary and the output directory.** The output directory is asked on every run and is
   the one question with no default. The confirmed agent's directory, as the user gave it, is offered as
   the suggested answer. Writing a folder is not installing it, so the skill never writes into an agent's
   directory unless the user names that directory.
4. **Writes the folder**, one per confirmed agent when there are several, each carrying only its own
   agent's keys. A written skill that takes input gets a prose input section that works on its own, so
   an agent that does not substitute an argument placeholder still has the contract. A key that turns
   automatic activation off is restated in the body, because an agent that ignores the key would
   otherwise activate the skill automatically.
5. **Verifies the files on disk**: the frontmatter parses, `name` and `description` are present, `name`
   equals the folder's name, the body is under 500 lines, and every cited `references/` path resolves
   inside the folder. Each failure names the file and the line. It never runs a repository's own check
   command.

Nothing is written before the summary and the output directory are confirmed. An unanswered agent
confirmation or output-directory question stops the run with nothing written, and an existing folder is
never overwritten without asking.

## Output

The run ends with every path written, each agent-specific value used, every agent-specific part left
out and where it would go, whether the new skill states an editing boundary, the result of each
verification assertion, and at least two requests that should start the new skill.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | An agent fact the user does not know is reported as a gap, never fetched. Every other input is the request, the conversation, or a file on disk. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | The files it writes are `SKILL.md`, reference files, scripts, and assets. |
| `Agent` | No step fans out. Detection is a handful of variable and directory checks. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(test:*), Bash(wc:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root before checking for configuration directories. |
| `Bash(test:*)` | Step 1, checking one environment variable at a time with `test -n`, and each configuration directory with `test -d`. |
| `Bash(wc:*)` | Step 5, counting a written `SKILL.md`'s lines to assert the body is under 500. |

All three commands only read. None of them changes a file.

**Creating directories is deliberately not pre-approved.** The output directory can lie outside the
working directory when the user names one, and leaving `mkdir` unapproved means each one prompts, so a
person sees every location the skill is about to write to.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
