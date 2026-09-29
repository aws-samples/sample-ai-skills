---
title: "Tool Grants"
sidebar_label: "Tool Grants"
sidebar_position: 3
---

# Tool Grants — research

Every skill under `skills/research/` declares two things in its frontmatter:

- **`disallowed-tools`** — a **denial set**, removing the capabilities that extend that skill's reach
  past what its body requires. This is the control.
- **`allowed-tools`** — a **pre-approval set**, confined to scoped `Bash(...)` commands. This bounds
  nothing; it exists to cut prompt fatigue.

The direction is the whole point, so it is stated before the tables: `allowed-tools` does not restrict
anything. A skill declaring a short `allowed-tools` list has not narrowed itself — every tool remains
callable. Read "What these declarations do not bound" below before drawing any conclusion from a
short list.

Each denial set was derived by reading that skill's body end to end, not from a summary table. The
rule is **remove what extends reach beyond the body's job; leave alone what the body merely happens
not to use today** — which is why `Read`, `Glob` and `Grep` appear in no denial set even where a body
does not obviously need all three. Denying `Grep` on `ai-create` because today's steps read named
files rather than searching would break the skill the first time a step reads by pattern, for no
security gain.

**There is no read-only skill in this set.** `ai-research` says "Research is read-only", and that
claim scopes to *application code* — the skill still writes `research.md`, may create a folder
README, and edits two manifests. `ai-archive` performs the set's only destructive, hard-to-reverse
filesystem mutation. Neither is denied `Write`.

## ai-create

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Denied explicitly rather than left implicit. |
| `Skill` | Step 7 *prints* the next `/ai-…` command for the user to run; it invokes nothing. |
| `NotebookEdit` | The only file written is a `README.md`. |
| `Agent` | No fan-out step. |

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Step 4.7 obtains the date prefix with `date +%F`, which the body insists be *run*, not recalled — a wrong-but-plausible date is invisible on inspection. |
| `Bash(mkdir:*)` | Step 6.1, `mkdir -p <output_root>/<derived-name>/`. |

No denied capability is used by this body.

## ai-research

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | The description reads "Research a codebase **or a topic**", which plausibly invites web research — but no step in the body fetches anything. This is the single largest untrusted-content surface in the set: attacker-controlled fetched text reaching the skill that writes a document two downstream skills treat as authoritative. Denied, not merely omitted. |
| `Skill` | No body invokes another skill. |
| `NotebookEdit` | The files written are `research.md` and, on the auto-create path, a folder `README.md`. |

`Agent` is **not** denied — Step 2b spawns four parallel Explore agents when the scope exceeds ten
files. `Write` and `Edit` are **not** denied; see the read-only note above.

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(git log:*), Bash(git show:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Context Loading resolves the folder with today's date from `date +%F`. |
| `Bash(mkdir:*)` | Context Loading's auto-create path. |
| `Bash(git log:*)`, `Bash(git show:*)` | Step 2's "Check git history for recent changes that provide context on design decisions" — read-only history, no mutation. |

`Bash(graphify:*)` is **deliberately absent**, and this is a decision rather than an oversight. Step
1b's `graphify query` is optional, the body degrades gracefully without it, and its output is content
the skill then reads *as findings* — so it is an untrusted-input surface, not merely a convenience.
Pre-approving it would remove the one prompt a consumer gets before an external tool runs across
their whole codebase. Stated cost: one permission prompt per run for consumers who use `graphify`. A
reviewer who finds the absence surprising should read this paragraph rather than add the entry.

No denied capability is used by this body.

## ai-plan

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | The closing section prints the next command; it invokes nothing. |
| `NotebookEdit` | The files written are `plan.md` and, on the auto-create path, a folder `README.md`. |
| `Agent` | `ai-plan` has **no fan-out step**, unlike its two neighbours. This is the one row that differs from `ai-research` and `ai-implement`. |

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(find:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Context Loading's folder resolution. |
| `Bash(mkdir:*)` | Context Loading's auto-create path. |
| `Bash(find:*)` | The ADR-log enumeration the body spells out literally: `find <log> -mindepth 1 -maxdepth 2 -name '*.md'`. |

`Bash(graphify:*)` is absent for the reason given under `ai-research`.

One limit worth naming here, because it is the clearest single illustration of the write-target gap
below: the body's strongest constraint is **"Read a status; never write one, and never write a
record"**, and that is **not expressible in either key**. `ai-plan` legitimately holds `Write` and
`Edit` for `plan.md`, so no declaration can stop it writing into an ADR log. That constraint is prose
and can only be prose.

No denied capability is used by this body.

## ai-implement

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | Where the body wants a plan, it tells the *user* to run `/ai-plan`; it invokes nothing. It also states that no ADR-authoring skill exists here. |
| `NotebookEdit` | No step names a notebook. |

`Agent` is **not** denied — Step 2b dispatches one agent per independent phase.

**`Bash` is not denied and is not scoped.** Step 3a installs "any packages the plan requires" and
Step 4.2 detects and runs an unknown project's test command from `package.json`, `pyproject.toml`,
`Cargo.toml`, or a `Makefile`. Any command allowlist here would be either a lie or a guess that
breaks the skill in the first repository using a different runner.

**Pre-approval set — none. This skill declares no `allowed-tools` key at all.**

That is the most consequential single line in these declarations, and it is a deliberate empty set
rather than an omission. No honest command scope can be written for a skill that runs an unknown
project's test runner, and a bare `Bash` entry here would auto-approve *every* command for the
invoking turn — before the consumer's permission callback is consulted, injected commands included —
on the skill most able to do damage. The correct pre-approval set is therefore the empty one: no key,
and the consumer's own permission prompts left intact.

**Said plainly: the denial set buys nearly nothing for this skill.** `ai-implement` is the skill
excessive agency is actually about, and it is the skill a tool-restriction mechanism helps least. Its
real bound is the write-path constraint in its body plus the harness's own permission prompt — not
anything on this page.

No denied capability is used by this body.

## ai-archive

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. |
| `Skill` | No body invokes another skill; there is no `/ai-unarchive`, and Step 10 prints the restore command instead. |
| `NotebookEdit` | The files written are two manifest `README.md` files. |
| `Agent` | No fan-out step — one folder per invocation, by design. |

`Write` and `Edit` are **not** denied: Step 7 deletes a manifest row with `Edit`, and Step 8 creates
or updates `<output_root>/.archive/README.md` with `Write`. This skill performs the set's only
destructive filesystem mutation, which is exactly why its declarations were derived from its body
rather than from any summary claiming it does not need write.

**Pre-approval set** — `Bash(date:*), Bash(mkdir:*), Bash(git rev-parse:*), Bash(git ls-files:*), Bash(git mv:*), Bash(mv:*)`

| Entry | Step behind it |
|---|---|
| `Bash(date:*)` | Steps 7 and 8 both take today's date from `date +%F`. |
| `Bash(mkdir:*)` | Step 5, `mkdir -p <output_root>/.archive/` — run before the move, because `git mv` fails when the destination's parent is absent. |
| `Bash(git rev-parse:*)` | Step 6.1, `git rev-parse --is-inside-work-tree`. |
| `Bash(git ls-files:*)` | Step 6.2, `git ls-files --error-unmatch`. |
| `Bash(git mv:*)` and `Bash(mv:*)` | Step 6's tracking branch — `git mv` on a tracked folder, plain `mv` otherwise. |

**Both move commands are pre-approved and neither is denied**, which is load-bearing rather than
convenient. The body's own analysis is that using the wrong one destroys the work: plain `mv` on a
*tracked* folder makes git record a deletion, so the archived content is absent from every future
checkout. Denying or failing to pre-approve either command would push the run toward the destructive
fallback Step 6 explicitly forbids.

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
| a wrapper script | the text matched is the wrapper's name |
| `sh -c 'git push …'` | the text matched is `sh` |

**The list is not closed.** Four of these are named explicitly in `ai-release`'s denial set; the
flag-reordering and wrapper-script cases remain open, and are recorded as open rather than
enumerated as though they were handled.

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
      "Bash(gh release:*)",
      "Bash(gh api:*)",
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
