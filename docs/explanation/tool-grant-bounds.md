---
title: "Tool Grant Bounds"
sidebar_label: "Tool Grant Bounds"
sidebar_position: 3
---

# Tool grant bounds

Every skill in this collection declares up to two keys in its `SKILL.md` frontmatter:

- **`disallowed-tools`** — a **denial set**, removing the capabilities that extend the skill's reach
  past what its body requires. This is the control.
- **`allowed-tools`** — a **pre-approval set**, confined to scoped `Bash(...)` commands. This bounds
  nothing; it exists to cut prompt fatigue.

Each skill's own page lists both sets under `## Tool grants`, with the reason for every entry. This
page holds what is true of all of them: what the declarations cannot bound, how a command scope is
matched, how those behaviours were established, and the settings a consumer can add for what no
frontmatter key expresses.

The direction is the whole point, so it is stated first: `allowed-tools` does not restrict anything.
A skill declaring a short `allowed-tools` list has not narrowed itself — every tool remains callable.
Read [What these declarations do not bound](#what-these-declarations-do-not-bound) before drawing any
conclusion from a short list.

## How a denial set is derived

Each denial set was derived by reading that skill's body end to end, not from a summary table. The
rule is **remove what extends reach beyond the body's job; leave alone what the body merely happens
not to use today** — which is why `Read`, `Glob` and `Grep` appear in no denial set even where a body
does not obviously need all three. Denying `Grep` on `ai-create` because today's steps read named
files rather than searching would break the skill the first time a step reads by pattern, for no
security gain.

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
- **`ai-implement`'s [write-path bounds](../skills/research/ai-implement/implementation-write-bounds.md)**,
  deriving the declared write set from the plan rather than from whatever the agent concludes mid-run.

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

**The list is not closed.** Three of `ai-scaffold-release`'s denial entries cover four of these rows:
`Bash(git send-pack:*)`, `Bash(curl:*)`, and the bare `Bash(gh:*)`, which covers both `gh` spellings
and every other subcommand of it — the gain from collapsing two scoped `gh` entries into one. The
flag, quoting, wrapper-script, and `sh -c` cases remain open, and are recorded as open rather than
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
looks: had a denial not reached subagents, every denial on a skill that fans out would be escapable
by dispatching a subagent to do the denied thing.

**The consequence, plainly.** If a future build collapses a specifier the way agent definitions do,
`ai-scaffold-release`'s four scoped entries would strip `Bash` entirely and break the skill. Nothing
in this repository can prevent that. What would catch it is a dry run of these skills on the next
release that touches them.

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
   either way. Largely moot for the skills that deny `Skill` — every skill except `ai-dev-autopr` —
   but the generalisation should not be made.

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

`Bash(git push:*)` is the line to copy if you want `ai-scaffold-release`'s no-push promise enforced
session-wide rather than only for the turn the skill runs in. Every caveat in
[A command scope matches text, not a program](#a-command-scope-matches-text-not-a-program) applies to
each of these entries too — a settings rule is matched the same way.

One limit carried forward from [What was not established](#what-was-not-established): a **managed**
settings allow rule was never tested against a skill denial, so which of the two wins under managed
policy is unknown.
