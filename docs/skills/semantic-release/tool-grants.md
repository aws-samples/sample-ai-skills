---
title: "Tool Grants"
sidebar_label: "Tool Grants"
sidebar_position: 3
---

# Tool Grants — semantic-release

The skill under `skills/semantic-release/` declares two things in its frontmatter:

- **`disallowed-tools`** — a **denial set**, removing the capabilities that extend that skill's reach
  past what its body requires. This is the control.
- **`allowed-tools`** — a **pre-approval set**, confined to scoped `Bash(...)` commands. This bounds
  nothing; it exists to cut prompt fatigue.

The direction is the whole point, so it is stated before the tables: `allowed-tools` does not restrict
anything. A skill declaring a short `allowed-tools` list has not narrowed itself — every tool remains
callable. Read "What these declarations do not bound" below before drawing any conclusion from a
short list.

This skill carries the only denials in the repository that do real security work, because its body
makes an explicit negative claim and these declarations make that claim structural instead of merely
written down. Elsewhere in the repository the denial sets remove network reach, skill invocation and
unused fan-out — all real, none of it touching the capability that carries the risk.

## ai-release

Its body states, at Step 6: **"Do not push this tag, a branch, or a release object."** The promote
half adds a second negative claim at Step 7c: installing the promote path promotes nothing, and every
push lives in the installed `scripts/promote.sh` rather than in the document.

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent, Bash(git push:*), Bash(git send-pack:*), Bash(gh:*), Bash(curl:*)`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | The body routes between its own two halves; it never invokes another skill. |
| `NotebookEdit` | The files it writes are a TOML config, shell scripts, a `Makefile`, CI configuration, and a `key=value` configuration file. |
| `Agent` | No fan-out step. |
| `Bash(git push:*)` | The no-push claim's most obvious spelling. |
| `Bash(git send-pack:*)` | The plumbing command that pushes without the word `push`. |
| `Bash(gh:*)` | A release object can be published through `gh` — `gh release create`, or `gh api` — with no `git push` anywhere. |
| `Bash(curl:*)` | The same, through arbitrary HTTP against the forge's REST API. |

**Four entries rather than one, and that is the actionable part.** `ai-release`'s job is to create a
release and to configure a path that publishes one. A single tidy `Bash(git push:*)` would leave the
no-push promise holed exactly where the skill's real work lives, because the forge's release object
never needs `git push` to reach it.

**The `gh` denial is bare rather than scoped, and that cost a step a command.** It was previously
`Bash(gh release:*), Bash(gh api:*)`, scoped so that the credential pre-flight could consult
`gh auth status`. The promote half denies the forge CLI as a capability rather than two of its
subcommands, so that pre-flight can no longer run it: Step 4 now reports the presence of
`GITHUB_TOKEN` and names `gh auth status` as the operator's own check. That is a real reduction in
what the pre-flight verifies, accepted deliberately — a skill that can configure a public publish
path should not also be able to publish a release object, and two scoped entries could not close
every subcommand that does.

**Pre-approval set** — `Bash(test:*), Bash(git remote:*), Bash(git tag:*), Bash(git log:*), Bash(git ls-remote:*), Bash(scripts/promote.sh:*)`

| Entry | Step behind it |
|---|---|
| `Bash(test:*)` | Step 4's credential pre-flight, testing for `CI_JOB_TOKEN`, `GITLAB_TOKEN` or `GITHUB_TOKEN`. Presence is reported; a value never is. |
| `Bash(git remote:*)` | Step 2.1, `git remote get-url origin` → forge topology. |
| `Bash(git tag:*)` | Step 2.2's `git tag --list`, and Step 6's `git tag -a` plus its `git tag -l` verification. |
| `Bash(git log:*)` | Step 2.4, `git log --format=%s` → how many existing subjects the parser would group. |
| `Bash(git ls-remote:*)` | Step 6's verification that `git ls-remote --tags origin` does **not** list the new tag. |
| `Bash(scripts/promote.sh:*)` | A dry run of the installed promote script, which reports and pushes nothing. |

Two things this pre-approval set does **not** do. It does not make a promotion reachable from the
skill: the dry run is pre-approved, and the underlying push stays denied, so the only thing the skill
can invoke is the reporting half of that script. And it is a path-prefixed scope, so it matches
neither `bash scripts/promote.sh` nor the same script named by absolute path — see "A command scope
matches text, not a program" below. Only the one spelling the body uses is declared.

Step 7b's `git ls-tree -r --name-only <tag>` is deliberately not pre-approved: it prompts, which
costs one approval on a step that is about to ask the builder two questions anyway.

The `-r` is what keeps that cost at one. A `PUBLISH_PATHS` entry may be nested, so the builder has to
see paths below the first level to write one — and descending interactively would spend this approval
once per directory instead of once. A single recursive print buys every candidate path for the same
one prompt and needs no new grant, since the scope that would cover it (`Bash(git ls-tree:*)`) is not
declared in either direction.

**What this is not.** The denial is structural against the spellings an agent normally writes, and
against compound commands. It is **not** a boundary around `git` or `gh`, because a `Bash(...)` scope
matches command text rather than the program invoked. See "A command scope matches text, not a
program" below for what evades it.

No denied capability is used by this body.

## What these declarations do not bound

A declaration in either direction is a **capability** list. It has no vocabulary for a **target**.
`Write` is deniable; "write only inside this repository", "write only the paths the plan names", and
"never write into the ADR log" are not expressible — not in `disallowed-tools`, not in
`allowed-tools`, not in a settings `permissions.deny` rule, and not in an agent definition's
`tools:`.

So the in-body constraints that bound write *location* are not complements to this mechanism. They
are the only controls that do that job at all, and nothing in the harness substitutes for either:

- an **edit-scope constraint** in each skill body, bounding writes to the session's repository or
  working directory;
- **`ai-implement`'s write-path bounds**, deriving the declared write set from the plan rather than
  from whatever the agent concludes mid-run.

Reading these declarations as a path sandbox is the worst available misreading, because it would
justify deprioritising those two as redundant — trading two real controls for one that cannot do
their job.

### A command scope matches text, not a program

`Bash(git push:*)` matches the **command text**, not the program invoked. It is therefore not a
security boundary around `git` or `gh`. Each of these evades a bare `Bash(git push:*)` denial unless
separately named:

| Spelling | Why it evades |
|---|---|
| `git -C . push origin main` | the scope's literal prefix no longer matches |
| `git -c push.default=current push origin main` | same — a flag sits where the scope expects `push` |
| `git 'push' origin main` | the quoting breaks the literal prefix |
| `git send-pack origin HEAD:main` | a different subcommand that pushes |
| `gh release create …` | publishes a release object with no `git` involved |
| `gh api …` | the same, through the REST API |
| `curl -X POST …/releases` | the same again, with no forge CLI either |
| a wrapper script | the text matched is the wrapper's name |
| `sh -c 'git push …'` | the text matched is `sh` |

**The list is not closed.** Four of `ai-release`'s denial entries cover five of these rows — the bare
`Bash(gh:*)` covers both `gh` spellings and every other subcommand of it, which is the gain from
collapsing the two scoped `gh` entries into one. The flag-reordering and wrapper-script cases remain
open, and are recorded as open rather than enumerated as though they were handled.

What works in the mechanism's favour: a denial fires when **any** subcommand of a compound command
matches, including inside a subshell, a command substitution, or a control-flow body. So
`git status && git push origin main` is caught — the naive evasion most likely to be reached for
does not work.

A **path-prefixed** scope is brittle in the opposite direction, toward *false* denial. A scope such as
`Bash(scripts/example.sh:*)` matches neither `bash scripts/example.sh` nor the same script named by
absolute path. Where a body spells one script two ways, both spellings must be declared.

### The pre-approval set bounds nothing

`allowed-tools` is per-turn permission **pre-approval**, not a restriction. Every tool stays callable
whether or not it is listed, and the entry clears on the next user message. Its only purpose here is
to cut prompt fatigue — itself a security concern, because a pipeline that prompts on every `date`
trains a consumer to approve without reading.

**The denial set is the control.** Do not read a short `allowed-tools` list as a narrow grant. In the
first draft of this work every "exclusion" from that list was a no-op, and a bare entry there is an
*elevation* of privilege: it auto-approves that whole tool before the consumer's permission callback
is consulted. That is why the conformance gate refuses any entry that is not a scoped `Bash(...)`.

## How these behaviours are known

Two behaviours this mechanism depends on were established by **probe against a single build**, and
the published documentation describes neither — its wording reads as though whole-tool removal were
the behaviour. They are recorded here as observed, not as promised.

**A scoped denial honours its specifier.** `disallowed-tools: "Bash(git push:*)"` denies only
matching calls and leaves `Bash` available. The two alternatives were **ruled out**, not merely
unobserved:

| Possible behaviour | Status |
|---|---|
| denies only matching calls; `Bash` stays available | **observed** |
| collapses to whole-tool removal | **ruled out** |
| scoped values silently ignored, nothing denied | **ruled out** |

The probe could separate the three because it ran in a repository with **zero remotes**, where an
unguarded `git push --dry-run` fails with git's own usage text. That makes an *executed* push
unmistakably distinguishable from a *denied* one, and `git tag --list` and `git log -1` both kept
working alongside the denial. Against a working remote, a silently-ignored denial and an honoured one
would have looked alike and the third row would have stayed open.

**A denial reaches dispatched subagents, asymmetrically.** Stated as two effects rather than one
claim about "propagation":

- in the **invoking session**, every call to the denied tool is *refused*;
- in a **subagent dispatched via `Agent`**, the tool is *absent from the pool*.

Established against a byte-identical control minus the denial line, in which both parent and subagent
wrote successfully and both files existed on disk — so the subagent's failure was the harness
withholding the tool, not the subagent failing for reasons of its own. This matters more than it
looks: had a denial not reached subagents, every denial on the two skills that fan out would be
escapable by dispatching a subagent to do the denied thing.

**The consequence, plainly.** If a future build collapses a specifier the way agent definitions do,
`ai-release`'s four scoped entries would strip `Bash` entirely and break the skill. Nothing in this
repository can prevent that. What would catch it is a dry run of these skills on the next release
that touches them.

### What was not established

Listed so a tested behaviour can be told from an assumed one:

1. **Whether a bare-name denial alters the invoking session's advertised tool schema**, or only
   refuses every call to it. The only evidence is model self-report, which is not evidence. "Every
   call refused" is established, and is all this mechanism relies on. Note the contrast with
   subagents, where tool *absence* **is** established.
2. **Whether a skill denial survives a *managed* settings allow rule.** A user-level settings allow
   does not override it (probe). Managed policy was not tested, so a consumer under managed policy
   may see behaviour this page does not describe.
3. **Whether a misspelled entry is logged in any channel not surfaced by `-p` or `--debug`.** Nothing
   appeared in either. "Silent" here means silent to the channels a consumer would actually look at,
   and no more than that.
4. **Whether a denial applies when a *subagent* invokes a skill through the `Skill` tool.** A
   different path from `Agent` dispatch, and the working `Agent` result must not be read as covering
   it — that path fails with a bare `<error>Execute skill: …</error>` which establishes nothing
   either way. Largely moot for these skills, since every one of them denies `Skill`, but the
   generalisation should not be made.

## The MCP residual — a limit, not a gap

A denial can only exclude a capability it can **name**. A consumer's session may carry arbitrary
`mcp__*` servers, so "this skill must not reach the network" is **not expressible**: deny `WebFetch`
and `WebSearch`, and `mcp__someserver__fetch` still answers.

This is not a gap to be closed. It cannot be closed, and a later reader who tries to complete the
denial set will add brittleness without adding coverage. It is also why the derivation rule is
"remove what extends this skill's reach past its job" rather than "deny the complement of what the
body happens to use".

## Recommended consumer-side settings

Some constraints no frontmatter key can express are expressible in a consumer's own settings. A
settings `deny` rule overrides `allow`, applies for the whole session rather than one turn, and is
**not** cleared by the next user message — unlike either frontmatter key.

```json
{
  "permissions": {
    "deny": [
      "Bash(git push:*)",
      "Bash(git send-pack:*)",
      "Bash(gh:*)",
      "Bash(curl:*)",
      "WebFetch",
      "WebSearch"
    ]
  }
}
```

`Bash(git push:*)` is the line to copy if you want `ai-release`'s no-push promise enforced
session-wide rather than only for the turn the skill runs in. Every caveat in "A command scope
matches text, not a program" above applies to each of these entries too — a settings rule is matched
the same way.

One limit carried forward from the list above: a **managed** settings allow rule was never tested
against a skill denial, so which of the two wins under managed policy is unknown.
