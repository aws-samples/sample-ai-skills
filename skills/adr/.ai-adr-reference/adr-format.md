# ADR Format Reference

Shared normative reference for the **decision log** — the directory of architectural decision records (ADRs) a project keeps, one short markdown file per architecturally significant decision. "Decision log" is `adr.github.io`'s own term for the collection, so this reference uses it rather than inventing a synonym.

`/ai-adr` writes and transitions records against every rule here, and it is the only writer. A **consumer** — any tool that reads the log rather than writing to it — needs only the log-path resolution and enumeration rules (§11), the five states (§5), the four reader tolerances (§6), and the status-to-authority mapping (§15). A consumer reads a status and never writes one. Whether a project's tooling gates on this log at all is that project's decision, and it belongs in a record rather than in this reference.

The length budget (§16), the provenance rule (§17), the filing move (§18), and the durability rules (§19) are **writer-only**, and named as such here so no consumer starts enforcing them. A reader that applied a 450-word cap or looked for a ` — *(inferred)*` marker would reject records already committed to the log — including AWS-shaped records written before this reference existed — and a consumer that never writes a record has nothing to gain from either rule.

Every rule cites the page or the script that establishes it. §14 names the two rules that are inferences rather than specifications.

| Source | Where |
|---|---|
| AWS process | `docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html` |
| AWS best practices | `…/architectural-decision-records/best-practices.html` |
| AWS FAQ | `…/architectural-decision-records/faq.html` |
| AWS appendix | `…/architectural-decision-records/appendix.html` |
| adr-tools | `github.com/npryce/adr-tools` v3.0.0 — cited by script name (`_adr_title`, `_adr_status`, …) |
| Nygard's template | the published template whose status list ends in "etc." |
| Nygard's post | "Documenting Architecture Decisions" (2011), the post that introduced the format |

`adr(1)`, the Ubuntu man page, is authority for the **command surface** only: its BUGS section calls the page a stub, and it names no directory, no `.adr-dir`, and no filename convention. Never cite it for a path.

## §1. When a decision earns a record

Write a record only for a decision affecting one of five categories, which AWS quotes from Richards and Ford 2020 (AWS process): **structure** (patterns such as microservices), **non-functional requirements** (security, high availability, fault tolerance), **dependencies** (coupling of components), **interfaces** (APIs and published contracts), **construction techniques** (libraries, frameworks, tools, processes).

Without the test, an agent asked to write an ADR writes one for any decision at all, and a log of fifty unrankable records is a log nobody reads.

## §2. The record's sections

AWS's example record (AWS appendix), in order: **Title**, **Status**, **Date**, **Context**, **Decision**, **Consequences**, **Compliance**, **Notes** (Author, Version, Changelog).

Compliance and Notes are AWS-specific and both mandatory — the AWS FAQ requires that "Each ADR must have a status and a changelog that contains the change date and the person who is responsible for the change", and Compliance records how adherence is verified.

**Considered alternatives go inside Context**, not in a section of their own: "The context should mention possible solutions the team considered" (AWS appendix). MADR's separate `## Considered Options` is a structural deviation — do not borrow it.

AWS's set is a **superset** of adr-tools' packaged template, which is Nygard's five sections (Title, Status, Context, Decision, Consequences) and nothing more. Adopting AWS therefore costs no interoperability, while adopting adr-tools' template would drop the two sections the FAQ mandates.

**Bullets are the default shape inside four sections** — Context, Decision, Consequences, and Compliance — under the per-section caps §16 fixes. This changes the shape of what goes inside four sections and changes the section set itself in no way: all eight stay mandatory, and considered alternatives stay inside Context rather than moving to a list of their own.

**The one place a bullet is illegal is the `## Status` keyword line.** `+ Accepted` is not exactly equal to `Accepted`, and `_adr_remove_status` deletes only the line *exactly equal* to the keyword — so a bulleted status survives removal untouched, a later supersession appends `Superceded by [...]` beneath it, and the record then asserts two states at once with nothing erroring anywhere. The status keyword sits alone on its own bare line, always (§4, constraint 4).

## §3. The Decision prose rule

AWS process: "The decision must clearly state, in imperative language, the solution the team has decided to adopt. Avoid using words such as 'should,' and phrase each decision to say 'We use…' or 'The team has to use…'"

Write `We use Postgres 16 for the ledger.` Reject `should` in this section — a decision phrased as a recommendation cannot be enforced, because nothing in it says the team is bound.

**The rule applies per bullet, not per section.** Once Decision is a list (§2), each bullet opens `We use` or `The team has to use`, and each is checked for `should` on its own. A section whose first bullet reads `We use Postgres 16 for the ledger` and whose second reads `we should probably pin the minor version` holds one decision and one suggestion, and the pinned version binds nobody.

## §4. Four positional constraints

adr-tools parses records with `head`, `cut`, and `awk` rather than a markdown parser, so its expectations are positional. A record that breaks one still renders in a browser while producing wrong output from a tool, which is why each constraint names its failure.

1. **First line is `# Title`, with no YAML frontmatter above it.** `_adr_title` is `head -1 | cut -c 3-`, so a leading `---` makes every title in a generated table of contents the two characters after the delimiter — in practice `-`. This is the constraint with teeth: MADR puts its metadata in frontmatter, so MADR's structure and adr-tools' tooling cannot both be used.
2. **`Date: YYYY-MM-DD` on the next content line.** adr-tools' template emits `Date: DATE` and substitutes `date +%Y-%m-%d`. No script parses the field, so this is convention rather than mechanism — it costs one line and matches AWS's Date section.
3. **Status is bare prose inside a `## Status` section, never a `Status: X` field.** `_adr_status` returns every non-blank line between `## Status` and the next heading. A record that writes the status as a field, or in frontmatter, is invisible to `adr` and to any parser modelled on it.
4. **The status keyword sits alone on its own line.** `_adr_remove_status` deletes the line *exactly equal* to the keyword, so `Accepted 2026-08-22` survives removal untouched: a later supersession appends `Superceded by [...]` and leaves the accepted line in place, and the record then asserts two states at once with nothing erroring anywhere. An acceptance timestamp goes on a separate line inside `## Status`, or in the changelog — never appended to the keyword.

## §5. The five states

| State | Source |
|---|---|
| `Proposed` | AWS process — the owner "provides the ADR in the **Proposed** state at the beginning of the process" |
| `Accepted` | AWS process; also the literal adr-tools substitutes at creation |
| `Rejected` | AWS process |
| `Superseded` | AWS process |
| `Deprecated` | Nygard's template |

Every value is published vocabulary, so this format **adds no status of its own** and has no status deviation to defend.

**Five states and no sixth.** A parking state — the one a user reaches for when a proposal is going nowhere and neither accepting nor declining it is true — was researched, recommended, and declined on 2026-08-20. No published ADR source names such a state, so adding it would put the set's only invented value in it; there is no verb for it either. The accepted cost: a proposal nobody reviews warns on every planning run until someone accepts it, declines it, or deletes it.

## §6. Reading a status — four tolerances

Every consumer applies all four. Each prevents the same failure, a **retired decision read as live**, which under §15's mapping stops a plan to comply with a decision the team already replaced.

1. **Match both spellings of superseded.** adr-tools writes "Super**c**eded" — `adr-new`'s supersede path calls `_adr_add_link "$target" "Superceded by"`. Match `Superseded` and `Superceded`.
2. **A supersession link with no keyword is superseded.** `_adr_remove_status` deletes the old keyword outright, so the retired record's Status section holds only `Superceded by [Title](file.md)` — no `Accepted` and no `Superseded` token for a keyword lookup to find.
3. **Read status as the prose body of `## Status`,** not as a field.
4. **Take the keyword case-insensitively from the section's first non-blank line.** A correctly-written record legitimately holds more than one line there — a keyword plus a link, or a keyword plus a timestamp — so a reader requiring exactly one line misreads it.

An unrecognised keyword is **reported once, naming the file and the value, and loaded as no constraint**. Both silent defaults fail: reading it as `Accepted` turns a typo into a hard gate on a decision nobody made, and reading it as absent lets a real decision quietly stop gating.

## §7. Immutability, as AWS scopes it

Two sources disagree, and the difference decides whether a lifecycle is implementable at all:

- **log4brains, unconditional:** "an ADR is immutable. Only its status can change."
- **AWS, scoped to post-acceptance (AWS process):** "The team should treat ADRs as immutable documents after the team accepts or rejects them."

Under log4brains' reading, AWS's own rework loop is illegal, because revising a `Proposed` record's Context mutates something other than its status. **This format follows AWS** — it is the authority this format traces to, and it names the boundary instead of implying one. The rule that follows:

- A **`Proposed`** record is a working document. Context, Decision, Consequences, and Compliance may be revised in place.
- An **`Accepted`** or **`Rejected`** record is frozen. Only the keyword and link lines inside `## Status` may change.
- A record's Context and Consequences describe the project **on the record's date**. A path or name in them that no longer exists is history, not an error, and is never a reason to edit, amend, or supersede the record (§19).

## §8. Transition legality, and the three refusals

A record is freely editable while `Proposed`; once `Accepted` or `Rejected` the only moves left are `Accepted → Superseded` and `Accepted → Deprecated`; every other change is a new record.

Two transitions are **refused as illegal moves**, and each refusal offers supersession or deprecation as the legal alternative:

- **`Accepted → Rejected`.** "Decline the X decision" is how a user asks to undo an accepted decision, and a silent status edit turns "we decided this and later changed our minds" into "we never decided this" — it erases the fact that the team decided it.
- **`Rejected → Accepted`.** The same boundary, other direction.

Deprecation is the move for an accepted decision that no longer applies with nothing replacing it. Without that state such a record has no legal move at all, which is why it is kept.

The third refusal is **distinct in kind** from those two, and confusing the two kinds produces the wrong message to the user. `Accepted → Rejected` and `Rejected → Accepted` are illegal moves — no input makes them legal. This one blocks a *legal* move on unresolved content:

- **`Proposed → Accepted` and `Proposed → Rejected` are refused while any bullet still carries ` — *(inferred)*`,** the marker §17 puts on a claim the agent concluded rather than read or was told. Acceptance must leave Context, Decision, Consequences, and Compliance byte-identical (§7), so the marker cannot be stripped during the transition — accepting with one in place freezes an unconfirmed claim into a record that then gates every plan under §15's mapping. The resolution is to confirm or drop the claim while the record is still `Proposed` and freely editable, then transition. The refusal names each unresolved bullet, so the user does not have to open the file to find them.

`Accepted → Superseded` and `Accepted → Deprecated` are outside this refusal: by it, an `Accepted` record holds no marker to find.

## §9. Immutability and the changelog, reconciled

The AWS FAQ mandates a changelog on every record; AWS best practices says where a change goes: "change the status of the old ADR to **Superseded**, note their changes in the change history of the *new* ADR, and keep the old ADR in the decision log."

So a change is recorded in the **new** record's changelog while the old record's status becomes `Superseded`. An agent that appends the explanation to an accepted record's own changelog has violated immutability while appearing to honour the changelog mandate. adr-tools implements the same reconciliation — its supersede path edits the old record's Status section and nothing else.

## §10. Who sets a status

**No skill sets a status on its own initiative.** A record moves only on an explicit human instruction.

One sanctioned exception: `/ai-adr` writes the log's own first record as `Accepted` on its first run in a repository, because invoking it on a repository with no log *is* the decision that record documents. `adr init` does the same. This is not a licence to self-accept anywhere else.

## §11. Resolving the log path, and creating a log

Three rules. **RESOLUTION** finds the log, **ENUMERATION** turns it into a list of records, and **CREATION** makes a new one. Conflating the first with the last creates a second log beside the one a project already has.

**RESOLUTION — every consumer.** Mirroring adr-tools' `_adr_dir`, walking up from the working directory and at each level:

1. **`.adr-dir` present** → its contents, resolved relative to the level that held it. Stop.
2. **an existing `doc/adr` directory** → that path. Stop.
3. otherwise ascend; at the filesystem root, **no log exists**.

Resolution ends at "no log exists", **not at a default path**. `_adr_dir` itself ends with a bare `echo doc/adr`, but a consumer handed a directory holding no records gains nothing from it, so every consumer treats the third outcome as *skip*.

**ENUMERATION — every consumer.** Resolution hands back a directory; this rule turns it into a list of records. A record is any `*.md` file at the log root **or exactly one directory below it** whose filename begins with a digit:

```sh
find "$ADR_DIR" -mindepth 1 -maxdepth 2 -name '*.md' | grep -E '/[0-9][^/]*\.md$'
```

The leading-digit test is `adr-list`'s own filename filter with the recursion depth raised from zero to one. It excludes `README.md` — the index (§13) — and a `templates/` directory's own template, while admitting both a dated name and an adopted sequential one (`0001-…`). Depth is bounded at one because the directories below a log are filing buckets (§18) rather than a tree, so nothing legitimate sits deeper.

**State the rule rather than leaving it implied.** A consumer that globs a single segment — `<log>/*.md`, matching files directly inside the log root and in no subdirectory of it — still finds every `Accepted` record, because §18 files those at the root. So the failure this rule prevents is not a broken hard gate. It is a **silent warn tier**: the `Proposed` records sit one level down, the consumer loads none of them, produces no warning, and reports nothing — which is indistinguishable from a project that has made no architectural decisions at all (§15).

**CREATION — `/ai-adr`'s first-run branch alone.** A new log goes at **`docs/adr`**, and `.adr-dir` records that path immediately.

**Why the two paths differ.** The probe reads `doc/adr` because that is where `adr init` with no argument writes, and where it writes no `.adr-dir` — so probing it is the only thing standing between a project that already keeps records there and a duplicate log at `docs/adr`. Creation uses the plural form because it matches the `docs_path` and `output_path` keys a project already has.

**`.adr-dir` is the only carrier of the log path.** It is `adr-init`'s own one-line file (`echo "$1" > .adr-dir`), an ordinary tracked file, so the path survives a fresh clone; `cat` is the whole parser; and the `adr` CLI honours it, so `adr list` works in a log these skills created. No frontmatter key participates — a project's context file holds nothing about the log, so nothing that writes one needs to change. Claim it as "the convention of adr-tools, the most widely packaged ADR toolchain, committed in roughly 300 public repositories", never as an ecosystem standard: no second tool reads it.

**Where a created log lands.** `docs/adr` nests inside a detected `docs_path` for Docusaurus, MkDocs, Jekyll, and the heuristic fallback, so in most consuming projects the records are published to the site, become sidebar entries, and fall under the link check that gates the docs build. Say so once on the first run, and name `doc/adr` as the alternative for a project that wants the log unpublished.

## §12. Filenames — a named deviation

Records are named `YYYY-MM-DD-description.md`. AWS specifies no filename convention, and `adr.github.io` — the source AWS refers naming to — specifies none either, so this deviates from no authority. It does diverge from the ecosystem's dominant sequential-number convention, so it is recorded here as a deviation with its costs.

- The **date is the creation date**, written once and never rewritten, matching `manifest-update.md:73` — the leading position is always the date, never a sequence number. Renaming on acceptance would break every inbound link and would itself mutate a record whose value is that it does not move.
- **Accepted downside: no short citable identifier.** Cross-references carry the full filename or the title, and number-keyed tooling does not apply — `adr-log`, the Backstage ADR plugin, and `@ADR(n)` annotations all key on the number.
- **Accepted downside: `adr new` must not be run.** Its allocator is `ls | grep -Eo '^[0-9]+' | sed -e 's/^0*//' | sort -rn | head -1`, so in a dated log the maximum is the *year*: a 2026 log yields `2027-<slug>.md`, sorting between real dates, with nothing erroring. Create records with `/ai-adr`; use the CLI for `list`, `generate toc`, and `link` only. `adr upgrade-repository` is untested here and excluded as a precaution rather than a demonstrated hazard.
- **Accepted downside: three of the four read commands narrow, and the fourth was already broken.** Once §18 files records by status, `list`, `generate toc`, and `link` see only the records at the log root — they glob a single segment. `generate graph` was already unusable against a dated log independently of filing, because it derives each node's identifier by deleting everything from the first hyphen onward, so every record created in one calendar year collapses into a single node.
- **A cross-record reference is a filename citation in backticks, never a markdown link.** Write `` `2026-08-20-record-architecture-decisions.md` ``. The one exception is the `## Status` supersession line, which §6 tolerance 2 requires as a link and §7 permits editing, so it is recomputed whenever either endpoint moves. The mechanism: a body link written from `proposed/` resolves relative to that directory and breaks the moment §18 moves the record to the log root — and an accepted record's body may not be edited to repair it (§7), so the broken link is permanent.
- On a **same-day slug collision**, ask. Never overwrite.

## §13. The index

The log's index is **`<log>/README.md`**, grouped under three headings in this order — `## Accepted`, `## Proposed`, `## Retired` — and listing **every record including retired ones**, because a rejection an agent cannot see is a rejection it proposes again.

The first two groups carry Date and linked title. **`Retired` carries a third column holding the exact status**, because it is one group covering three states (§18): collapsing them would lose the difference between a decision the team declined and one it replaced, which is the part a reader years later cannot reconstruct.

**Links are relative to the log root**, so a filed record's link carries its directory segment — `proposed/2026-08-25-file-records-by-status.md` — while an accepted record's link carries none.

**A record's own `## Status` section wins over the index.** The index is a derived convenience and the record is the source, so a disagreement is **reported** naming the file, the group it was listed under, and the keyword — and never resolved by editing a record to match the index.

`/ai-adr` maintains it on every write and every transition, carrying the same update-on-every-write obligation the working manifest does (`manifest-update.md`). It must be a **committed file** rather than generated on demand, because what routes an agent to it reads a file from disk and cannot run a command.

`adr generate toc` is useful as a drift check, but it emits `* [$title]($link)` with **no status column** and reads only the log root (§12) — so a check extracts titles and links from both sides and compares them against the `## Accepted` group alone, or it reports a difference on every run and gets ignored.

## §14. Two labelled inferences

The changelog itself is an **AWS mandate** (AWS FAQ). Two rules about its contents are **inferences from AWS's example rather than specifications**, and are presented as such wherever they appear:

- **Bumping the version to `1.0` on acceptance.** AWS mandates a version and shows `0.1: Initial proposed version`, but never states the bump.
- **Putting the rejection reason in the changelog row.** AWS requires the reason — the owner "adds a reason for the rejection to prevent future discussions on the same topic" — and does not say where it goes.

## §15. Consumers: absence is normal, and status maps onto the existing ladder

A project with **no log is the normal case**. A consumer skips **silently** when resolution finds none, because a warning on every run in a project that has made no architectural decisions is noise.

When a log resolves, each record's status maps onto the constraint authority ladder a consumer already runs for the `*(inferred)*` marker. No second mechanism:

| Status | Authority |
|---|---|
| `Accepted` | Behaves as a **confirmed** constraint — stop and revise |
| `Proposed` | Behaves as an **inferred** constraint — warn, name the record, continue |
| `Rejected`, `Superseded`, `Deprecated`, log4brains' `draft` | Not a constraint. Load nothing, print nothing |
| anything else | Not a constraint, reported once with the filename and the value (§6) |

Name the record **by filename** in every warning and every stop, so the user can open it. There is no short identifier to cite — that is §12's accepted cost.

## §16. Record altitude — the length budget

**Writer-only.** `/ai-adr` obeys this section; no consumer enforces it. This section fixes how long a record is; §19 fixes the level of abstraction each bullet is written at.

"One short markdown file" is an adjective, and an adjective loses to any specific rule pointing the other way. So the budget is numbers:

| Section | Cap | Shape |
|---|---|---|
| Context | 6 bullets | one per constraint; one per rejected alternative, with its reason on the same bullet |
| Decision | 5 bullets | each opens "We use" — §3's phrasing rule survives bulleting unchanged |
| Consequences | 6 bullets | each outcome bullet prefixed `Positive:` or `Negative, accepted:`, at least one of each; a bullet carrying §17's marker states an unresolved risk and takes the marker in place of a prefix |
| Compliance | 4 bullets | each a real check, or the literal `Not yet defined: <what is unverified>` |
| Any bullet | 30 words | one claim plus one consequence clause |
| The four body sections together | 450 words | headings excluded. Notes sits outside the budget: Author, Version, and the Changelog are AWS-fixed structure whose rows carry a date, a person, and a reason |

A **prose paragraph** is permitted only where a bullet cannot carry the claim, and at most one per section. Two paragraphs in a section is the section reverting to prose.

**The altitude, stated because `voice.md` reads like a prohibition on this.** That standard requires preserving analytical depth — "compress the prose, never the analysis" — and states that removing a concept to satisfy it is a failure of it. At record altitude the depth rule is satisfied by **naming a consequence in a clause rather than explaining it in a paragraph**: the concept is kept, the paragraph is not. A record states a decision and what follows from it; the reasoning that produced it lives in the interview the record came out of and in whatever artifacts the project keeps.

**The cut-order.** A budget met by deleting a real accepted downside is worse than an over-long record, so what gets cut is specified rather than left to judgement.

Cut first, in this order:

1. **Content restating this reference's own mechanics.** A record explaining why `adr new` allocates from the calendar year duplicates §12 at the reader's expense — and the duplication compounds, because the record and the reference then drift apart.
2. **Editorial connectives** — "it is worth noting that", "with that said", a sentence whose whole job is introducing the next one.
3. **The same fact stated in two sections.** Keep it where it is load-bearing and drop the echo.

Never cut:

- **A rejected alternative and the reason it was rejected.** AWS requires Context to mention the solutions the team considered, and a rejection an agent cannot see is a rejection it proposes again.
- **An accepted downside.** A record listing only upsides reads as advocacy, and the downside is the part a reader years later cannot reconstruct.
- **A consequence for whoever acts on the decision** — what changes, for a person or for a tool that reads this log, once this record is `Accepted` (§15). This is the bullet that makes a record actionable rather than descriptive: a record stating only what was decided leaves a reader with nothing to do differently.

**No offloading.** A record stays self-contained on its project-specific content, so it cannot meet the budget by citing a pipeline artifact for its reasoning: working folders get archived, and a project may gitignore its working root outright, so the cited path may be absent from a fresh clone and the record then points at nothing. Naming a tracked source file is different — it ships with the clone — but a record must also survive the file being edited, moved, or renamed, so a citation follows §19: no line numbers, and no path where a stable name will do.

## §17. Provenance of a record's claims

**Writer-only**, like §16.

A record is read years later by someone holding none of today's context, so a claim the agent concluded and a claim the user supplied must not look alike on the page. Every bullet in a record falls into one of three classes:

| Class | How it appears | Example |
|---|---|---|
| The user said it | plain bullet, no marker | "the team has no operational experience with it" |
| A file shows it | plain bullet naming what was read, at the most stable level §19 allows | "No data store is provisioned in `infra/` today" |
| The agent concluded it | bullet suffixed ` — *(inferred)*` | "Query latency under the reporting load is untested at this size — *(inferred)*" |

**Silence means confirmed**: an unmarked bullet is a confirmed one and a derived one carries the suffix, the same reading a constraint bullet gets in any project context file. That default is safe only under the strict converse, which is the rule: **an unmarked bullet must trace to the user's words or to something the agent read in the tree on the record's date**, named per §19, and anything that traces to neither takes the suffix. The claim still has to come from a file the agent read; it no longer carries a line range to prove it, because the record's `Date:` and the repository's history at that date locate the source and do not go stale.

**The literal suffix is ` — *(inferred)*`** — em dash, a space either side of it, the word italicised in parentheses. This reference owns that spelling. A constraint bullet in a project context file such as `AGENTS.md` carries the same one, so there is one vocabulary, and a user who has met the marker there already knows what it means and that confirming the claim clears it by deleting the suffix.

**A marker is resolved while the record is `Proposed`** and therefore freely editable (§7). It never survives into `Accepted` or `Rejected`: §8's third refusal blocks that transition while one is outstanding, because acceptance leaves the body byte-identical and would freeze the unconfirmed claim into a record that gates every subsequent plan.

**No asserted deliberation.** AWS requires Context to mention the solutions the team "considered", and a source listing options is a menu rather than deliberation — a dependency file naming three queue libraries is not evidence anyone weighed three queue libraries. An alternative the user did not name is either asked about or omitted, and never written as considered. Writing one in fabricates a discussion, and the record then closes a question the team never opened.

**No unsourced quantities.** A number in a record traces to the user or to a cited file, or it does not appear at all. An invented "roughly 40% of requests", added to make a Context bullet concrete, becomes the figure a later decision is argued from — and no marker fixes it, because the problem is that the quantity has no source rather than that its source is the agent.

## §18. Filing records by status

**The move is writer-only** — `/ai-adr` performs it. Every consumer inherits only §11's ENUMERATION rule, and reads no directory name.

A flat log gives a directory listing no status signal: `ls` cannot tell a decision that binds a plan from one the team rejected months ago. Filing answers that without adding a second source of truth.

**The keyword is authoritative; the path is derived.** A consumer reads status from `## Status` and from nothing else. That is what holds a consumer's change to the single enumeration sentence §11 specifies, and it is why an invented directory cannot quietly become a sixth state (§5) — it produces a report instead.

| Status | Location |
|---|---|
| `Accepted` | the log root |
| `Proposed` | `<log>/proposed/` |
| `Rejected`, `Superseded`, `Deprecated` | `<log>/retired/` |

**Why `Accepted` sits at the root rather than in `accepted/`.** The layout is asymmetric on purpose. A consumer that never learned §11's rule globs one segment, and against this layout that glob returns exactly the binding records — so an un-upgraded reader keeps its hard gate. Under a symmetric layout the same glob returns nothing, the reader loads zero constraints, and it reports nothing, which is indistinguishable from a project that has made no decisions. Both layouts fail an un-upgraded reader somewhere; this one chooses where.

**`retired/` holds three states because §15 gives all three identical authority** — `Rejected`, `Superseded`, and `Deprecated` each load nothing and print nothing. The name is a filing bucket rather than a status: **the state set stays five**, and `Retired` is not one of them. Two of the three could not be filed by keyword anyway, because a record the `adr` CLI superseded holds only `Superceded by [Title](file.md)` and no keyword at all (§6 tolerance 2).

**A transition edits the keyword first and moves the file second.** The order is the recovery property. After the edit, a half-applied transition leaves the authoritative carrier correct and only the address stale — which the invariant below reports and a `git mv` repairs. The reverse order leaves a record asserting its old status from its new address, where the wrong carrier is the authoritative one.

| Transition | Move |
|---|---|
| `Proposed → Accepted` | `proposed/X.md` → `X.md` |
| `Proposed → Rejected` | `proposed/X.md` → `retired/X.md` |
| `Accepted → Superseded` | `X.md` → `retired/X.md` |
| `Accepted → Deprecated` | `X.md` → `retired/X.md` |

Use `git mv` inside a repository and `mv` outside one, in the same commit as the keyword edit so git records a rename and `git log --follow` reaches across it. **Only the directory changes.** The filename is fixed — its date is the creation date (§12) — so a move is never a rename.

**Directories are created on demand.** Git does not track an empty directory, so a seeded `proposed/` would need a `.gitkeep` to survive a clone, and nothing else in the log needs one.

**Records already in a log are never migrated.** Filing applies to what `/ai-adr` writes or transitions. A log adopted under §11 keeps its existing records exactly where they are, and the resulting mixed layout is **reported once** — the same shape as the one-off report for an adopted log using sequential filenames (§12).

**The invariant.** For every record §11 enumerates, the directory implied by its keyword equals the directory it sits in. Report each disagreement naming **the file, the directory, and the keyword**, and treat the keyword as correct. Read the keyword under §6's four tolerances, so a record holding only a supersession link files under `retired/`. A keyword §5 does not name is reported as unrecognised and **not filed**, because moving it would need a destination this map has no entry for.

**Why this is specified here rather than scripted.** Only the skill trees are distributed, so a check living in a repository's `scripts/` directory is absent from every consuming project — and one of the two runtimes is a prompt runtime with no guaranteed shell. The invariant is therefore a step `/ai-adr` performs on every run, and it costs nothing extra: §13's index pass already enumerates the log.

## §19. Durability — writing a record that survives refactoring

**Writer-only**, like §16–§18. It governs what `/ai-adr` writes, and nothing a consumer reads changes.

An `Accepted` record is frozen (§7), and the code it describes keeps changing. A bullet that says *where* something sits in the tree is true on the record's date and false after the next refactor, and nobody may correct it. A line citation goes stale fastest: the next edit above the cited line moves it. Nygard's post names the subject of a record: "Each record describes a set of forces and a single decision in response to those forces." A file location is at most evidence for a force.

**The rename test.** Before writing any bullet, ask: *would a rename, move, or refactor that leaves the decision intact make this bullet false?* If yes, rewrite the bullet at a higher level, or drop it. Every rule below applies this test.

**Name things in order of stability.** When a bullet has to name something, use the most stable name available:

| Tier | Example | Where it may appear |
|---|---|---|
| 1. Technology, standard, or policy | Postgres 16, RDS Multi-AZ, Conventional Commits, "every schema migration" | Every section. Preferred everywhere |
| 2. Component or tool role | "the ledger database", "the deploy pipeline", "the CI base image" | Every section. Tiers 1 and 2 are the only tiers allowed in `## Decision` |
| 3. Stable identifier | CI job `infra-plan`, test `test_ledger_schema`, command `make checks`, config key `DB_ENGINE` | Compliance, to name the check. These change far less often than file layout |
| 4. File or directory path, no line | `infra/`, `infra/main.tf` | Context only, when naming the file helps a reader and it has no stable equivalent |
| 5. `path:line` or `path:start-end` | `infra/main.tf:1-40` | Never, in any section |

When a Context claim really depends on an exact snapshot of a file, pin it to a commit rather than a line: `` `infra/main.tf` at `98cbf59` ``. A commit-pinned citation stays accurate for as long as the record is frozen. Use it rarely and only in Context, because the record's `Date:` already dates every Context bullet.

**Decision bullets name choices, not places.** A Decision bullet opens "We use" (§3) followed by a tier-1 or tier-2 name, and names no file, directory, function, or line. When the decision really is about a location, name the location's role and keep the path out:

```markdown
+ We use the repository root, not a subtree of the internal tree, as the home of the documentation.
```

not:

```markdown
+ We use `internal/docs/maintainer/` for maintainer-facing pages.
```

The second form is false as soon as the implementation chooses a different directory, and a `Proposed` record then needs rewriting before it can be accepted. The first form stays true.

**Context is a dated snapshot.** Context and Consequences describe the project on the record's date (§7). A reader who finds a path that no longer exists is reading history, not an error.

**Compliance states an invariant and names its check.** Each Compliance bullet has two parts: *what must stay true*, at tier 1 or 2, and *what enforces it*, at tier 3.

```markdown
+ Exactly one database instance with engine `postgres` is declared; the `infra-plan` CI job asserts it.
```

not:

```markdown
+ `infra/main.tf:12` declares an `aws_db_instance` with engine `postgres`.
```

The first bullet becomes false only when the decision is broken, which is a finding a person can act on. The second becomes false when line 12 moves, and it then reports a violation while the decision is still being followed. `Not yet defined: <what is unverified>` (§16) is unchanged.

**The check cites the record; the record does not cite the check's location.** Where a check enforces a decision, the check's own docstring or comment names the record **by filename, with no directory**:

```python
"""Enforces 2026-08-20-use-postgres-for-the-ledger.md: exactly one postgres instance is declared."""
```

A record's filename is never renamed (§12), and filing (§18) changes only its directory, so a filename-only reference from code to record is correct for as long as the record exists. The reference sits in a file anyone may edit, and whoever edits the check maintains it. The record's side names the check by its tier-3 identifier and needs no maintenance. `/ai-adr` writes only to the log, so it cannot add that docstring. It names the step in its report instead, and a consumer that writes a check to enforce an `Accepted` record cites the record's filename in that check.

**A moved path is never a reason to change a record.** Supersede only when the decision changes. Nygard's post: "It's still relevant to know that it *was* the decision, but is *no longer* the decision". A renamed file changes no decision. When the code and an `Accepted` record disagree, the fix goes in the code or in a follow-up task, never in the record. AWS best practices: "you can either update the outdated code base or artifacts gradually, while introducing new changes, or your team can decide to refactor the code explicitly by creating technical debt tasks."
