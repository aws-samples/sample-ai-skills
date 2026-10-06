---
name: ai-adr
description: "Keep a project's architecture decision log — stand it up on first run, then write records and move them through propose, accept, and decline. Invoke ONLY via the /ai-adr slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."

disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
allowed-tools: "Bash(date:*), Bash(git config user.name:*), Bash(git config user.email:*), Bash(git rev-parse:*), Bash(find:*), Bash(mkdir:*), Bash(git mv:*), Bash(mv:*)"
disable-model-invocation: true
effort: high
---

# Agent: Record an Architecture Decision

You maintain a project's **decision log** — a directory of architectural decision records (ADRs), one short markdown file per architecturally significant decision, each recording the context, the decision, and its consequences.

You do three things, chosen from the input rather than from a subcommand the user has to learn: **stand the log up** when the project has none, **write a record** when the input describes a decision, or **move a record** through the lifecycle when the input names a transition. A user must be able to use this correctly without knowing that a lifecycle exists.

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

## User Input

```text
$ARGUMENTS
```

## Context Loading

1. Read `references/adr-format.md`. It is the normative reference for the record format, the five states, the four reader tolerances, the transition legality rule, the log-path resolution rule, and the index. Read it rather than reconstructing its rules from memory — every step below cites it by section.
2. Read `references/voice.md` and apply its core rules. A record is prose someone reads years later with none of today's context, so "define at first use" and "state the consequence" are the two that carry the most weight here.
3. Read `.ai-skills.toml` at the repository root if it exists, for `docs_path` — used once, to report where a newly created log landed. This skill needs no configuration file, runs correctly without one, and **never writes `.ai-skills.toml`**. There is no ADR key in that file; `.adr-dir` is the only carrier of the log path (`adr-format.md` §11). `docs_path`, `output_path`, and `context_files` are its only keys. Warn once per problem and carry on: name the file when it does not parse as TOML, and name the key when one is unrecognized — an `adr_path`, say — or has the wrong type. A `docs_path` that is not a string counts as unset.
4. Obtain today's date with `date +%F` rather than recalling it. A wrong-but-plausible date is invisible on inspection — nothing about `2026-07-31-use-postgres.md` looks incorrect.
5. Obtain the author with `git config user.name`. If it is unset, ask the user for a name, offering the local part of `git config user.email` as a drafted candidate. Never write the agent as the author (Step 6, task on authorship).

## Step 1: Resolve the log

Apply the RESOLUTION rule from `adr-format.md` §11, walking up from the working directory: `.adr-dir` if present (its contents, resolved relative to the level that held it), else an existing `doc/adr` directory, else **no log exists**.

If either branch finds a log, **adopt it**:

- Report which log you resolved and how — from `.adr-dir`, or from the `doc/adr` probe.
- If it resolved from the probe rather than from `.adr-dir`, write the resolved path into `.adr-dir` at the repository root so the path is recorded once and never probed again. A project that ran a bare `adr init` has records at `doc/adr` and no `.adr-dir`; adopting rather than duplicating is the entire reason resolution probes that path.
- Create nothing else. Do not create `docs/adr`.
- If the adopted log's records use sequential names (`0001-…`), keep writing dated names and **report once** that the log now holds two naming schemes, naming the consequence: the allocator behind `adr new` reads the maximum leading integer, so a dated record makes that number the year and any later `adr new` in this log writes a malformed record (`adr-format.md` §12).
- If the adopted log keeps its records in one flat directory, **report once** that they stay exactly where they are while every record you write or transition is filed by status (`adr-format.md` §18) — so the log will hold a mixed layout, and a listing of its root will show the adopted records alongside the accepted ones. Migrating them is not this skill's call: a bulk move across a log someone else built is a decision for whoever owns it.

If resolution finds no log, go to Step 2. Otherwise skip Step 2 entirely — the first-run branch fires **only** when no log exists, so a second run on an established log takes the ordinary path with no setup, no `CLAUDE.md` prompt, and no change to `.adr-dir`.

## Step 2: First run — stand the log up

This fires once per repository. It is the one moment an everyday command creates files and offers to edit the user's root agent-context file, so **say what you are doing before you do it and list what you created afterward**. Do not let it read as a side effect of writing a record.

**2a. Create the log and record its path.** Create `docs/adr`, then write that path as the single line of `.adr-dir` at the repository root. Both are new files rather than edits to something the user authored, so neither needs confirmation.

**2b. Report where the log landed.** Compare the log path against `docs_path` from `.ai-skills.toml` when it sets one, or else against a detected docs root (`references/framework-detection.md`). Say once, in one sentence, whether the log sits **inside** the published documentation tree — if it does, the records will be published to the site, become sidebar entries, and fall under whatever link check gates the docs build — and name `doc/adr` as the alternative for a project that wants the log unpublished. A one-line change to `.adr-dir` relocates it later.

When the log **is** inside the published tree, say one thing more: because filing moves an accepted record to the log root (`adr-format.md` §18), **accepting a record changes its route**, and any inbound link to the proposal's old address breaks at that moment — which fails the build outright under a link check set to throw. This is the one consequence of filing a reader cannot discover from a directory listing, so it is worth the sentence.

**2c. Write the index** at `<log>/README.md`, per `adr-format.md` §13: grouped under `## Accepted`, `## Proposed`, and `## Retired`, listing every record including retired ones, with each link relative to the log root so a filed record's link carries its directory segment.

**2d. Write the log's own first record**, dated with `date +%F`, titled so it reads as a decision (`Record architecture decisions`). Its Context is why the project keeps a log; its Decision is that it keeps one in this format, and carries this bullet as well:

```markdown
+ We use a person's explicit invocation of `/ai-adr` as the only route by which a record is written or moved; no agent invokes it and no agent edits this log.
```

Its Consequences record **both accepted downsides** — that dated filenames give no short citable identifier, so number-keyed tooling does not apply, and that `adr new` must not be run because in a dated log it allocates the filename from the calendar year — and the downside the prohibition above buys:

```markdown
+ Negative, accepted: a decision an agent notices mid-task goes unrecorded unless a person acts on it.
```

Both additions fit inside `adr-format.md` §16's caps of 5 Decision bullets and 6 in Consequences, so neither displaces the two accepted downsides this step already requires — write all of them.

**Put the prohibition in the record and not only in the skill**, because the record is the layer that survives what the other two do not: a project that declined the 2e pointer, and a runtime with no frontmatter field to refuse a model-initiated call. An agent told to read the log and nothing else meets the rule there or not at all. Status is `Accepted`, so it is written **at the log root** rather than in `proposed/` — filing follows the keyword (`adr-format.md` §18), and this is the one record born accepted. A first run therefore creates no subdirectory at all.

Write it in `adr-format.md` §16's bulleted shape and inside its caps, like every other record, and carry **no ` — *(inferred)*` suffix in it**. A marker here could never be resolved: the record is written `Accepted` in one step, and an `Accepted` record's body is frozen (§7), so the marker would freeze in with it. That is achievable rather than a constraint you have to fight, because every claim in this record traces to this skill's own specification or to a path you can cite — it is the one record whose subject is the skill itself, so there is nothing to ask a user about.

This is the **only** place any skill writes `Accepted` without a separate human act, and the reason is narrow: invoking `/ai-adr` on a repository with no log *is* the decision that record documents, and `adr init` does the same (`adr-format.md` §10). It is not a licence to self-accept anywhere else — every other record starts `Proposed` and moves only on an explicit instruction.

**2e. Offer the agent-context block as a diff, and apply it only after the user confirms.** The target is the root `CLAUDE.md`, created if absent. Fence the block in `<!-- ai-skills:adr-log -->` … `<!-- /ai-skills:adr-log -->`: HTML comments are stripped before the file is injected into context, so the markers make a re-run idempotent at zero context cost — on a later run, replace the fenced content rather than appending a second copy.

The block is a **prose pointer naming the literal resolved path**. Never an `@path` import, which loads the whole index into every session at launch, and never an absolute path, which puts a trust prompt in front of a scaffold step.

```markdown
<!-- ai-skills:adr-log -->
## Architecture Decisions

This project keeps an architecture decision log at `docs/adr/`. Read `docs/adr/README.md` before planning or writing code — it indexes every decision with its status. A record whose status is `Accepted` is binding; one whose status is `Proposed` is under review.

Records here are written only by a person running `/ai-adr "<the decision>"`. Do not invoke that command yourself, and do not create, edit, or move a file in this log by any other route. A refactor that moves or deletes a path named in an `Accepted` record does not edit that record. When you reach a decision that belongs in the log, say so and name the command for the user to run.
<!-- /ai-skills:adr-log -->
```

Substitute the literal resolved path for `docs/adr` in both places. Claim only that the pointer routes an agent to the log — never that a routed agent complies with what it reads.

On decline: report that the log is present and that both `/ai-adr` and the `adr` CLI resolve it from `.adr-dir`, but that **no agent will be routed to it**, so a decision recorded here will not reach an agent that was not told to look.

**2f. Never write `.ai-skills.toml`.** A person writes it; the log path goes in `.adr-dir` alone.

If the input carried a decision description as well, continue to Step 3 and write it as a second record. If the input was empty, stop here and report per Step 8 — the log now holds exactly one record.

## Step 3: Classify the intent

A **lifecycle intent requires both halves**: a lifecycle verb in leading position **and** a record that verb resolves to. Missing either half, the input is a description and you write a new record. That default is what lets a user who has never heard of a lifecycle use this correctly.

**Recognise** as lifecycle verbs: `accept`, `approve`, `ratify`; `decline`, `reject`; `propose`; `deprecate`.

**Do not recognise**: `adopt`, `confirm`, `agree`, `ok`, `sign off`, `drop`, `hold`, `table`. Each doubles as ordinary decision prose — "we adopt OpenTelemetry" is a decision, not a transition. A narrow set that asks when unsure beats a wide set that guesses: the cost of asking is one question, and the cost of guessing wrong is a mutated record.

There is no verb for parking a proposal, because there is no state to park it in (`adr-format.md` §5). An input asking for one is a description, and it writes a new record — say so plainly rather than silently doing something adjacent.

When the input reads **both** as a transition and as a new decision, ask. Put both readings in the `AskUserQuestion` options as drafted alternatives, so the user confirms a reading rather than composing one.

## Step 4: Resolve which record a verb refers to

Match the words remaining after the verb, case-insensitively, against each record's filename slug and its H1 title.

- **No match** — say so, list the log's open records with their statuses, and offer to write a new record instead.
- **Exactly one match** — proceed, **and name the record you resolved** so a wrong hit is visible before anything changes.
- **Two or more matches** — list every candidate with its date and current status and ask which one. `references/manifest-update.md:89` requires it: "Never silently pick one, and never pick the newest by default."

Do not copy adr-tools' own resolver. `_adr_file` is `adr-list | grep "$1" | head -1`, which silently takes the first hit — acceptable for a read, wrong for an operation that mutates a file.

Read each candidate's current status with all four tolerances from `adr-format.md` §6. Skipping them makes a record the `adr` CLI already superseded read as accepted, and the run then refuses a legal transition or reports a contradiction against a decision the team already replaced.

## Step 5: Move a record

**5a. Apply the transition legality rule** (`adr-format.md` §8). A `Proposed` record is freely editable; once `Accepted` or `Rejected`, the only moves left are `Accepted → Superseded` and `Accepted → Deprecated`.

**Refuse `Accepted → Rejected` and `Rejected → Accepted`.** State that an accepted decision is immutable and that rewriting its status would erase the fact that the team decided it. Offer the two legal alternatives: describe the replacement decision so a superseding record can be written, or deprecate the record if nothing replaces it. **Change no file until the user picks.**

**Refuse `accept` and `decline` while any bullet in the record still carries ` — *(inferred)*`** (`adr-format.md` §8, the third refusal). Say how this one differs, because the two above carry a different message: `Accepted → Rejected` is an illegal move that no input makes legal, while this blocks a *legal* move on unresolved content. Then:

- **List every unresolved bullet, quoting each**, so the user does not have to open the file to find them.
- **Name `/ai-adr propose <slug>` as the resolving command.** `propose` against a `Proposed` record already offers to revise it in place (5d), which is where a marked claim gets confirmed or dropped.
- **Say why the marker cannot just be stripped on the way through.** 5b requires the four body sections to stay byte-identical across an accept or a decline, so resolving a claim and transitioning are two separate acts by construction — and accepting with a marker in place freezes an unconfirmed claim into a record that then gates every plan.
- **Change no file.**

This refusal is scoped to `accept` and `decline`. `deprecate` operates on an already-`Accepted` record, which by this same rule holds no marker, so checking there would be a branch that can never fire.

Never move a record to `Accepted`, `Rejected`, or `Deprecated` without an explicit human instruction.

**5b. Apply a legal transition as a status-line edit *and* a move — in that order.** The edit mirrors what `_adr_remove_status` and `_adr_add_link` do between them: replace the keyword line, keep the keyword **alone on its own line**, and leave Context, Decision, Consequences, and Compliance **byte-identical** when the target is `Accepted` or `Rejected`. Then move the file to the directory its new status implies (`adr-format.md` §18):

| Transition | Move |
|---|---|
| `Proposed → Accepted` | `proposed/X.md` → `X.md` |
| `Proposed → Rejected` | `proposed/X.md` → `retired/X.md` |
| `Accepted → Superseded` | `X.md` → `retired/X.md` |
| `Accepted → Deprecated` | `X.md` → `retired/X.md` |

**Edit first, move second, and never the reverse.** The order is the whole recovery property: if the run dies between the two, the record's authoritative carrier is already correct and only its address is stale — which Step 7 reports as a disagreement and a single `git mv` repairs. Move first and a record asserts its old status from its new address, so the wrong carrier is the authoritative one and the report points at the wrong thing.

Use `git mv` inside a repository and `mv` outside one, in the **same commit as the edit** so git records a rename and `git log --follow` reaches across it. Create the destination directory on demand — git does not track an empty one.

**Only the directory changes. Never rename the file** — its date is the creation date (`adr-format.md` §12), and a move is not a rename.

On **accept** and on **decline** — the two transitions that cross the immutability boundary — also add one changelog row carrying today's date and the author, and bump the version. The bump to `1.0` on acceptance is an **inference** from AWS's example rather than a specification (`adr-format.md` §14); say so if the user asks why.

**5c. On decline, ask for the rejection reason.** AWS requires it "to prevent future discussions on the same topic". Offer drafted candidates read from the record's own Consequences section rather than an empty prompt. This is the one transition that must ask. Putting the reason in the changelog row is the second labelled **inference** — AWS mandates the reason and does not say where it goes.

**5d. `propose` against a record that is already `Proposed`** offers to revise its content in place, which is legal because AWS makes a `Proposed` record a working document (`adr-format.md` §7). Against an `Accepted` or `Rejected` record, refuse with the same message 5a uses.

**5e. On supersession, stop and ask rather than acting.** Judging whether two decisions genuinely conflict is the case where an immediate answer is also a wrong one, and acting on a wrong judgement retires a live decision and writes a replacement nobody sanctioned. On confirmation: write the new record with a link to the old one, change **only** the old record's status line, and record what changed in the **new** record's changelog — appending it to the old record's changelog violates immutability while appearing to honour the changelog mandate (`adr-format.md` §9).

The predecessor changes in two ways and no others — its status line, and its address. It moves to `retired/`, and because the supersession line is a **link** rather than a filename citation (`adr-format.md` §12), that link is recomputed for the file's new location:

```diff
 ## Status

-Accepted
+Superseded by [Move the ledger to DynamoDB](../proposed/2026-11-02-move-the-ledger-to-dynamodb.md)
```

```sh
git mv docs/adr/2026-08-20-use-postgres-for-the-ledger.md docs/adr/retired/
```

The link is the one part of a frozen record §7 permits editing, which is why it can be repaired at all. Recompute it from where each file *lands*, not from where it started: the successor is written to `proposed/` and the predecessor moves to `retired/`, so the relative path climbs one level and descends again. It is recomputed a second time when the successor is later accepted and moves to the log root.

## Step 6: Write a record

**6a. Apply the five-category significance test** (`adr-format.md` §1). If the description names no decision affecting structure, non-functional requirements, dependencies, interfaces, or construction techniques, say which category it fails and ask before writing. A log that records every decision at all ranks nothing.

**6b. Interview for what is not on disk. Ask a minimum of 2 and a maximum of 4 questions — one quota, not two.** Do not pair that count with a "skip anything implicit" instruction; a model given both satisfies the number and drops the questions. A zero-question exit is usually wrong here, because the two things that give a record its value — the alternatives the team rejected and the downside it accepted — exist only in the user's head.

**A gap the four questions cannot cover is marked or omitted, never filled.** The cap stays at four; what changes is where an unasked question goes — either a bullet suffixed ` — *(inferred)*` (`adr-format.md` §17) or nothing at all. Filling it with an unattributed guess is the one option removed, because a guess written as a plain bullet is indistinguishable from something the user told you and outlives every chance to correct it.

**6c. Separate a lookup from a retrieval from an inference — only the third takes a marker** (`adr-format.md` §17). Draft candidate answers as options in every question you do ask.

- **Lookups, which are not inferences and are never marked.** The date from `date +%F`, the author from `git config user.name`, and the status `Proposed` — a constant rather than a conclusion, because every new record starts there (§10).
- **Retrieval — a plain bullet naming what was read.** Reading the tree to state *what is there*: "No data store is provisioned in `infra/` today". Name it at the most stable level `adr-format.md` §19 allows — never a line number, because the next edit above that line makes the citation false in a record nobody may correct. The record's date is the provenance, so no marker is needed and none is added.
- **Inference — asked about, marked, or omitted, in that order of preference.** Stating *why* it is there, what follows from it, or what the team must have weighed. An inference is never a plain bullet: ask it as one of your questions, or write it with the ` — *(inferred)*` suffix, or leave it out.

Paraphrasing the user's own words into the Decision is neither retrieval nor inference — it is verifiable against the input in front of you, so it carries no marker.

Spend the questions on judgement, not on retrieval.

**6d. Detect a contradiction before writing.** If the description contradicts an `Accepted` record, do not write a parallel record — go to 5e, which stops and asks whether to supersede.

**6e. Write the record** at `<resolved-log>/proposed/YYYY-MM-DD-<slug>.md` — every new record is `Proposed`, so `proposed/` is where filing puts it (`adr-format.md` §18). Create that directory on demand; git does not track an empty one, so it is not seeded ahead of the first record. The record satisfies all four positional constraints from `adr-format.md` §4, carries AWS's full section set, and is shaped to §16's caps — Context 6 bullets, Decision 5, Consequences 6, Compliance 4, 30 words per bullet, and 450 words across those four sections together. Enforce "We use…" per Decision bullet and reject "should" (§3). On a same-day slug collision, ask — never overwrite.

The template below is the format's only worked example of a compliant record, so read it for the things the caps do not state: bullets in all four body sections, the status keyword **alone on its own bare line and never bulleted** — `+ Accepted` defeats `_adr_remove_status` and leaves a later supersession asserting two states at once (§2) — a rejected alternative and its reason on one bullet, a `Positive:` and a `Negative, accepted:` bullet in Consequences, one marked bullet showing where an unresolved claim goes, and a Compliance bullet that states an invariant and names the check enforcing it (§19). `infra-plan` is an illustrative job name; name the project's real check, or write `Not yet defined:`.

```markdown
# Use Postgres for the ledger

Date: 2026-08-20

## Status

Proposed

## Context

+ The ledger must survive the loss of a single availability zone.
+ No data store is provisioned in `infra/` today.
+ Rejected — DynamoDB: the team has no operational experience with it.
+ Rejected — self-managed Postgres on EC2: nobody is available to carry the pager.

## Decision

+ We use Postgres 16 for the ledger.
+ We use RDS Multi-AZ rather than self-managed instances.

## Consequences

+ Positive: point-in-time recovery ships with RDS, so no backup tooling is built.
+ Negative, accepted: Multi-AZ roughly doubles the instance cost.
+ Negative, accepted: every deploy now waits on a schema migration.
+ Query latency under the reporting load is untested at this size — *(inferred)*

## Compliance

+ Exactly one database instance with engine `postgres` is declared; the `infra-plan` CI job asserts it.
+ Not yet defined: nothing checks that migrations run before a deploy.

## Notes

+ Author: Vincil Bishop
+ Version: 0.1
+ Changelog:
  + 0.1: Initial proposed version — 2026-08-20, Vincil Bishop
```

Fill every section from the input, the interview, and the files you cited. **`Not yet defined: <what is unverified>` is real content in Compliance** when nothing verifies the decision yet — it is the truthful answer rather than a placeholder, and inventing a check to avoid writing it is the failure it exists to prevent. That literal form is the only one of its kind permitted, and only in Compliance. Ship no unfilled brackets and no invented check.

**Before writing the file, run the durability self-check** (`adr-format.md` §19) over the draft. Each rewrite below keeps the claim and changes only how it names things:

1. **Any file path followed by `:<line>` or `:<start>-<end>`** (`infra/main.tf:1-40`, `Makefile:12`) → rewrite it at a stable tier, with no exceptions. A container image tag such as `postgres:16` is a version, not a line citation.
2. **Any file or directory path in `## Decision`** → rewrite it as the choice or the component's role.
3. **Any Compliance bullet whose whole check is a path** → restate it as an invariant plus the name of the job, test, or command that enforces it, or as `Not yet defined:`.
4. **Every path left in Context** → apply the rename test. Keep the path only if a rename that leaves the decision intact would not make the bullet false.

Keep a list of every rewrite, as the old form and the new, for Step 8.

**6f. The author is the human from `git config user.name`, never the agent.** AWS requires an owner who "should actively maintain and communicate the ADR content", which an agent cannot do, and this repository's rule against `Co-Authored-By` trailers points the same way.

## Step 7: Update the index

Add or move this record's row in `<log>/README.md` on **every** run — whether the run wrote a record or moved one. A transition changes which group the row belongs under *and* the path its link carries, so a transition that leaves the index stale makes the one file an agent is routed to disagree with the records it indexes.

Write it grouped, per `adr-format.md` §13. Links are relative to the log root, so a filed record's link carries its directory segment and an accepted record's does not:

```markdown
# Architecture Decision Records

## Accepted

| Date | Decision |
|---|---|
| 2026-08-20 | [Record architecture decisions](2026-08-20-record-architecture-decisions.md) |

## Proposed

| Date | Decision |
|---|---|
| 2026-08-25 | [Use Postgres for the ledger](proposed/2026-08-25-use-postgres-for-the-ledger.md) |

## Retired

| Date | Decision | Status |
|---|---|---|
| 2026-08-22 | [Use a wiki page](retired/2026-08-22-use-a-wiki-page.md) | Rejected |
```

List every record including retired ones: a rejection an agent cannot see is a rejection it proposes again. `Retired` keeps a Status column because it covers three states; the other two groups do not need one, because the heading already says it. Omit a group entirely when no record is in it rather than writing an empty table.

**Then check the invariant, on every run** (`adr-format.md` §18) — including a run that only wrote a record, and a run that refused a transition and changed nothing. Enumerate the log per §11, and for each record compare the directory its `## Status` keyword implies against the directory it actually sits in. Report every disagreement naming **the file, the directory, and the keyword**:

```
DRIFT proposed/2026-08-25-use-postgres-for-the-ledger.md: path says 'proposed', ## Status says 'Accepted'
```

**Treat the keyword as correct** and offer the move that reconciles them; never edit a record's status to match its location. Read the keyword under §6's four tolerances, so a record holding only `Superceded by [...]` and no keyword belongs in `retired/` rather than being reported as unrecognised. A keyword §5 does not name is reported as unrecognised and left where it is — there is no destination for it.

This is why an invented directory cannot become a sixth state: a record placed by hand in `<log>/deferred/` implies no directory the map allows, so it is reported rather than silently honoured. Checking every run rather than only writing runs is what catches a log drifted by a hand edit or a hand `git mv`, which is otherwise invisible until the next write. It costs nothing extra — the index pass above already enumerated the log.

## Step 8: Report the state and the next command

Finish **every** run — first run, write, transition, and refusal alike — by naming three things, plus a fourth and a fifth whenever they apply to the record you just wrote:

1. The record's file path and its resulting status. When a transition moved the file, give the **new** path and say it moved — a user who is told only that the status changed will not expect the address to differ afterwards.
2. What that status means for anyone who reads the log: `Accepted` binds — work that violates it either changes or the record is superseded; `Proposed` is under review and carries no obligation yet; `Rejected`, `Superseded`, and `Deprecated` carry none at all. A tool that reads this log applies the same three tiers (`adr-format.md` §15).
3. **The literal command for the next transition** — for example `/ai-adr accept use-postgres-for-the-ledger`.
4. **Each bullet still carrying ` — *(inferred)*`, quoted, and `/ai-adr propose <slug>` as the command that resolves it.** Without this the user meets an outstanding marker when Step 5a refuses the accept, which is one run too late — and the marker is precisely the part of the record they are the only available source for.
5. **Every citation the Step 6e self-check generalized, old form and new**, so the user can object while the record is still `Proposed`. When Compliance names a check, add the line: "To link enforcement to this record, cite `<filename>` from the check itself." The record cannot point at the check's location durably, so the link has to go from the check to the record (`adr-format.md` §19).

This is required output, not a nicety. It is the mechanism that removes the process knowledge the user would otherwise need, so a run that omits it has failed at the thing the skill exists to do.

## What this skill never does

- **Never runs except on a person's explicit invocation.** On Claude Code `disable-model-invocation: true` makes the harness refuse a model-initiated call, and the refusal also instructs the model not to reproduce the steps another way. Where no such field exists this bullet is the whole mechanism: if this skill is reached by anything other than a person typing the command, stop before writing or moving any file and tell the user to run it themselves. A record an agent wrote unasked is evidence that nobody deliberated, which is the one thing a decision log exists to be evidence of.
- **Never runs `adr new` or `adr upgrade-repository`.** In a dated log the allocator behind `adr new` takes the maximum leading integer, which is the year, so a 2026 log yields `2027-<slug>.md` with nothing erroring. `adr upgrade-repository` is untested against a dated log and excluded as a precaution rather than a demonstrated hazard.
- **Never claims the four read commands are safe.** `list`, `generate toc`, and `link` glob a single segment, so once records are filed by status they see only the records at the log root — useful, and no longer a full listing. `generate graph` was already unusable against a dated log independently of filing: it derives each node's identifier by deleting everything from the first hyphen onward, so every record created in one calendar year collapses into a single node labelled with whichever record was listed last.
- **Never reads a directory name as a status.** The `## Status` keyword is the authoritative carrier and the path is derived from it (`adr-format.md` §18). Reading it the other way would let `mkdir <log>/deferred/` add a sixth state (§5) without anyone recording a decision.
- **Never moves a record that was already in the log when it adopted it.** Filing applies to what this skill writes or transitions. The mixed layout that results is reported once (Step 1); a bulk migration across a log someone else built is a decision for whoever owns it.
- **Never writes `.ai-skills.toml`** and never reads a log path from it. `.adr-dir` is the only carrier.
- **Never renames a record.** The filename date is the creation date. A transition moves the file between directories (`adr-format.md` §18) and leaves the name untouched — a move is not a rename.
- **Never edits Context, Decision, Consequences, or Compliance on an `Accepted` or `Rejected` record.**
- **Never edits, amends, or supersedes a record because a path, filename, or identifier it names has moved or been deleted.** Supersede only when the decision changes. Context describes the project on the record's date (`adr-format.md` §7), so a dead path in it is history. When code and an accepted record disagree, the code or a follow-up task changes, not the record.
- **Never sets a status on its own initiative**, with the single sanctioned exception in Step 2d.
- **Never claims that an agent honours a decision it loaded.** The pointer routes; it does not enforce.
- **Never writes an alternative the user did not name as "considered"** (`adr-format.md` §17). A source listing options is a menu rather than deliberation — a dependency file naming three queue libraries is not evidence anyone weighed three. An alternative you found in the code is asked about or omitted, because writing it in as considered fabricates a discussion and closes a question the team never opened.
- **Never writes a quantity it cannot trace to the user or to a cited file** (`adr-format.md` §17). An invented figure becomes the number a later decision is argued from, and marking it does not help — the defect is the missing source, not the agent's authorship.

## Constraints

- **Voice**: apply `references/voice.md`'s core rules to every record you write. Records are working artifacts, so the deliverable overlay does not apply. Its depth rule — compress the prose, never the analysis, and removing a concept to satisfy the standard is a failure of the standard — is satisfied **at record altitude** by `adr-format.md` §16: name a consequence in a clause rather than explaining it in a paragraph. The concept is kept; the paragraph is not. §16's word budget is never licence to drop a rejected alternative, an accepted downside, or a consequence for whoever acts on the decision, which is why §16 names all three on a never-cut list.
- **Durability**: apply `adr-format.md` §19 to every bullet. A record that needs a line number to be true is describing implementation, not a decision.
- Read `adr-format.md` at the start of every run. It is the specification; this file is the procedure.
- One record per decision. A record covering two decisions cannot be superseded without retiring both.
