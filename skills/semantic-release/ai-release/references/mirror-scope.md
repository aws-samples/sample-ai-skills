# Promote scope

`PUBLISH_PATHS` in `.promote-target` is an allowlist: only the paths named there
ship to the public target. Anything not named is withheld, with no action
required to withhold it — a new directory added later is withheld automatically
until someone deliberately adds it to the list.

A path's **name** is never what withholds it. The filter matches paths against
the allowlist and nothing else, so a file whose name reads as internal, placed
under a path the allowlist names, ships.

## The allowlist binds at every depth

An entry may name a path at any depth, and may name a directory or a single
file. `docs/guides` and `docs/index.md` are both entries. There is no depth
limit, deliberately: refusing a deep entry would leave an operator either
publishing its siblings or reshaping the tree, and the first of those is
over-exposure — so a cap on an *allowlist* pushes toward the failure the
allowlist exists to prevent.

Where an entry names a path inside a directory the allowlist does not itself
name, that directory is published **partially**. The named descendants ship;
every sibling not named, at that level or below it, is withheld by the same
absence that withholds an unnamed top-level path. The filter removes a withheld
path at the shallowest level at which it can be named, so the list never has to
enumerate files individually.

The property to hold onto: **the allowlist is not weaker below the first level.**
Adding a directory inside a partially published one withholds it, exactly as
adding a top-level directory does.

## Allowlist, not denylist — and the reasoning holds at every depth

This is the inverse of a denylist. A denylist's failure mode is silent
over-exposure: a forgotten exclusion ships by default. An allowlist's failure
mode is silent under-exposure: a forgotten inclusion is merely missing from
the published tree. The second failure is the one worth having — an
incomplete public tree is a bug report waiting to be filed; an over-exposed
one is a disclosure that already happened.

Nesting does not weaken that argument, and it is the reason the configuration
gained no second key. A denylist *inside* a shipped tree — `PUBLISH_PATHS=docs`
plus an exclusion for `docs/internal` — would invert exactly this reasoning at
exactly the depth it matters: the dangerous case is a **new, never-named**
sibling appearing beside the exclusions, and no refusal can detect one.

What nesting does change is who carries the burden. Under a partially published
directory it moves to whoever adds **public** content: a new page there does not
ship until a line names it. That is accepted rather than discovered, and it is
why the dry-run report names, for every directory the filter descended into, what
that level left behind. Read the `withheld under <dir>:` blocks — they are the
difference between that failure being quiet and it being silent.

A consequence worth knowing before publishing part of a documentation tree: a
relative link from a published page to a withheld one still resolves internally
and breaks in the public tree. The promote path neither detects nor rewrites it;
`references/promote-extensions.md` §7 gives the shape of the repository-owned gate
that checks it.

## Deciding the allowlist — at configure time, not per publish

**The allowlist decides what ships from the tag's tree, and nothing else ships.**
A promotion publishes one commit built from that filtered tree, whose only parent
is a commit the target already holds, so none of the internal history behind the
tag reaches the target. What a withheld path held in some earlier revision does
not change what the allowlist exposes. The history audit is therefore
**optional**.

Run `scripts/history-probe.sh <tag-or-ref> <candidate-path>...` when the question
is about history itself: the internal repository may one day be published by some
other route, or the target already carries ancestry pushed by an earlier,
amending version of the promote script (`references/promote-extensions.md` §4).
The probe reports, per path, the earliest commit at which it is still readable in
that ref's reachable history and the largest size it ever reached — not merely
its current size, which is systematically the smallest instance a path ever had.

The probe is an audit the skill runs during configuration, and it is never
installed into the target repository. It is not a gate: no promotion consults
it, nothing acknowledges its findings, and a run of `assets/promote.sh` neither
invokes it nor requires that it ever ran. The predecessor's per-publish gate
contradicted this script's own header, which always described it as an audit.

This skill does not propose a default allowlist and does not decide which
paths are safe to publish. That decision is the operator's, made against the
tag's tree for this specific repository.

## An allowlist that does not describe the tag's tree refuses the run

There is no count assertion. `assets/promote.sh` verifies instead that **every**
entry in `PUBLISH_PATHS` describes the tree at the tag being promoted, and
refuses naming the offending entry.

That is strictly stronger than counting entries, and it catches the same
mistake the count was written for: a missing separator merging two entries into
one produces a token that names no path in the tree, so the existence check
refuses it. It also catches what a count could not — an entry naming a path
that simply is not there, which a count passes because it counts entries rather
than paths.

An entry fails to describe the tree in four ways, and they are **one** refusal
rather than four, because they are four answers to one question:

| The entry | Example |
|---|---|
| names a path the tag's tree does not contain, at any depth | `docs/gudies` |
| has an ancestor component that is a file, not a directory | `README.md/index.md` |
| is already shipped whole by an ancestor entry | `docs/guides`, beside `docs` |
| is malformed — a leading or trailing separator, an empty component, or a `.` or `..` component | `/docs`, `docs/`, `docs/../internal` |

The base therefore still carries **three** refusals, unchanged by accepting nested
entries, and none of them encodes a policy the installing repository has not
stated. A malformed entry is refused before any tag is resolved, since its fault
needs no tree to see: the same refusal arrives whether the tag was named or
derived, and a repository with no tag at all still gets the real reason.
