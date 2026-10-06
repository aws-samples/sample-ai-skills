# Promote extensions — the checks the base does not carry

`assets/promote_cli.py` carries three refusals. Its predecessor carried nine. The six
that came out are not rejected ideas; each encodes a policy that only the
repository installing the path can state, and their absence from a fresh install
is **silent**. This file is what makes the removal a relocation rather than a
loss: one section each, saying what the check did, why it is not in the base, and
the shape of the replacement.

Section 7 is not one of those six. It was never in the predecessor: it is a
consequence of publishing part of a directory, which the allowlist now permits,
and it is here for the same reason the other six are — the base deliberately does
not police it, and a repository that wants it policed needs the shape.

## Where a replacement goes

There are exactly two places, and the distinction is not stylistic.

| Put it in | When |
|---|---|
| `scripts/promote-gates.sh` — the gate hook | the check must run **inside the push transaction**, against the repository and the tag as they are at the moment of promotion |
| `needs:` on the promote job | the check is a **scan, a policy service, or an approval** — something the pipeline already runs, or a human, whose result is a job status |

A scan wants the pipeline's own tooling, caching, artifacts, and reporting, and
re-running it from inside the hook buys a slower copy with no report. An approval
is a person, and a person does not belong inside a shell script's exit status. A
divergence check, conversely, is meaningless a stage earlier: what matters is the
remote's state now.

### The hook's authority, stated once

`promote_cli.py` runs `scripts/promote-gates.sh` **if it is present and executable**,
after the confirmation is accepted and before anything is pushed, with `TAG` and
`PUBLIC_TARGET` exported to it.

- It is **executed, never sourced.** It runs in a subshell and only its exit
  status is read.
- **Non-zero refuses the run.** Nothing is pushed.
- **An absent hook is not an error.** A present, non-executable one is *reported*
  rather than silently skipped — it does not run.
- It **cannot** set the confirmation, clear the dry run, or cause a push that
  would not otherwise happen. A dry run exits before the hook is reached at all,
  so a hook assigning `CONFIRM_SHA` changes nothing.

Its only effect on a run is refuse-or-continue. That is deliberate and is the same
class of closure as parsing the configuration instead of sourcing it: a value that
authorizes a push may only arrive from the operator's environment.

**No fragment directory.** A repository needing two checks writes two functions in
one file. `promote-gates.d/` buys ordering nobody asked for and adds a failure
mode — a fragment without the executable bit silently does not run.

## 1. Origin pairing → the gate hook

**What it checked.** That the live `git remote get-url origin` equalled a
configured internal origin URL, compared as a full URL and never by remote name,
before anything was fetched from the public target.

**Why it is not in the base.** It asserts a fact a CI checkout already
establishes, and on a workstation it asserts the operator's remote naming rather
than anything about the tag. Its real purpose — telling a fork from a
legitimately-behind public copy — only mattered because the ancestry test below
existed. `.promote-target` therefore carries no key for it.

**The replacement.** In `scripts/promote-gates.sh`:

```sh
EXPECTED=git@internal.example:group/project.git
[ "$(git remote get-url origin)" = "$EXPECTED" ] || {
  echo "refusing: origin is not the configured internal origin" >&2; exit 1; }
```

Compare full URLs. Two projects in one namespace can share a remote leaf name and
differ only by an inserted path segment. See `references/provenance.md`.

## 2. Tip-parent ancestry → the gate hook

**What it checked.** That `merge-base(tag, public/main)` equalled the public
tip's **direct parent** — not merely was an ancestor of it — so the public tip was
exactly one publish behind the tag being offered.

**Why it is not in the base.** It encodes an ancestry policy, and it is the check
most likely to fail closed on a truncated graph, which is what trains operators to
bypass a gate. `references/provenance.md` has the full reasoning, including why
ancestry cannot substitute for identity.

**There is no replacement, because the check can no longer match.** The public
commit is built from the filtered tree with `git commit-tree`, and its only parent
is a commit the target already holds. The public line therefore shares no commit
with the internal one, so `merge-base(tag, public/main)` is empty and a hook
comparing it refuses every promotion. What the check protected — a public tip that
is not one publish behind — is now a question about the public tip alone, and §3
is where it is answered.

## 3. Divergence → the gate hook

**What it checked.** That the public tip held nothing the internal line lacked,
by comparing the two trees path by path and excluding deliberate internal
removals.

**Why it is not in the base, and what replaces it structurally.** The base makes
a narrower guarantee that needs no comparison: **it never overrides a tip it did
not build on.** `promote_cli.py` builds the public commit on a parent it names in the
dry run, and pushes one `--atomic` lease expecting exactly that parent, with no
fallback. The parent is the remote-tracking ref for the target when the clone has
one — the record of what this clone last promoted, which only a push writes — and
otherwise the target's current tip, read with `ls-remote` and adopted.

Measured against git 2.54.0:

| This clone's record | Target branch | Parent, and the lease | Result |
|---|---|---|---|
| none | absent | none — a root commit; the lease expects no branch | **succeeds**, the first publish |
| none | exists | the target's tip, adopted; the lease names that tip | **succeeds** |
| matches the target | exists | the record; the lease expects the record | **succeeds** |
| stale (a commit landed after the record) | exists | the record; the lease expects the record | **refused**, `stale info` |

The second row is the one to read twice. Adoption is what lets the first
promotion onto a target holding an initial commit succeed, and **a fresh clone has
no record**, so every CI promotion takes that row. In CI, then, a commit someone
else put on the target — an external contribution merged there — becomes the
public commit's parent, and the promoted tree replaces its content. The lease
still refuses a tip that moves between the read and the push, and `--atomic`
keeps the tag from landing alone when it does.

Two consequences to read together rather than separately:

- **The base reports; it does not judge.** The dry run's `parent:` line names the
  commit a promotion will build on and where that commit came from. Nothing in the
  base decides whether that commit belongs there.
- **Divergence is refused only from a clone that holds a record** — a workstation
  that made the previous promotion. A repository that promotes from CI and wants
  an external contribution refused rather than built on adds the hook below.

**The replacement**, for a repository that wants divergence *detected and named*
rather than merely refused, is the hook — because only there is the remote's
current state the thing being judged:

```sh
git fetch -q "$PUBLIC_TARGET" main:refs/promote/public
ORPHANS="$(comm -23 \
  <(git ls-tree -r --name-only refs/promote/public | sort) \
  <(git ls-tree -r --name-only "refs/tags/$TAG" | sort))"
[ -z "$ORPHANS" ] || { echo "refusing: public holds content the tag lacks:" >&2
  printf '  %s\n' "$ORPHANS" >&2; exit 1; }
```

## 4. The history-exposure gate → neither; it is a configure-time audit

**What it checked.** That the history probe had run and produced a report for
every withheld top-level path, plus an `ACK_HISTORY_EXPOSURE` acknowledgement
when the probe found a withheld path readable anywhere in the reachable history.

**Why it is not in the base.** It was a configure-time audit expressed as a
per-publish gate. The probe's own script header always described it as an audit
run while choosing the filter, and the gate reading it contradicted that by
requiring it to have run inside every publish.

**The replacement is not a gate at all.** `scripts/history_probe_cli.py` lives in
this skill and runs **while the allowlist is being chosen**, reporting per path
the earliest commit at which it is still readable and the largest size it ever
reached. It is never copied into a target repository. See
`references/mirror-scope.md`.

Worth stating plainly, because the gate obscured it: **a promotion publishes no
internal history.** The public commit is written from the filtered tree with
`git commit-tree`, its author and committer are the publisher identity, its
message names only the tag, and its only parent is a commit the target already
holds. No internal commit, internal subject, author address, or past revision of
a withheld path is reachable from anything pushed. What the probe reports is
therefore history a promotion does **not** carry, and running it is optional. It
still answers two questions: what would be exposed if the internal repository
itself were ever published by some other route, and what an earlier promotion
already exposed (below).

**A target promoted to by an earlier version of this script already carries that
history.** That version amended the tag's commit, and an amended commit keeps its
parents, so each push sent the tag's whole ancestry. The current script builds on
that target's tip and does not rewrite it. Removing it is manual and is the
repository's decision: a new public repository, or a force-push of a
single-commit branch holding the current tree, with every old tag deleted from the
target. To see what such a target holds, fetch its tags into a namespace of your
own — `git fetch "$PUBLIC_TARGET" 'refs/tags/*:refs/promote/public-tags/*'`, never
into `refs/tags/`, where they would collide with the internal tags of the same
name — and run the probe against them.

A repository that nonetheless wants a withheld path's history refused on **every**
publish — because that history will reach the public by another route — puts it
in the gate hook. It reads the repository at promotion time, so it is a hook
concern and never a job dependency:

```sh
# Every path the tag's tree holds, at every depth, with the ones that ship removed.
# THE RECURSION IS NOT COSMETIC: PUBLISH_PATHS entries may be nested, so a
# top-level listing reads a PARTIALLY published directory as fully withheld and
# refuses on the ancestry of paths that do in fact ship. Compare a path against
# every entry that could cover it — the entry itself, or any ancestor of it.
ships() {
  local path="$1" entry
  while IFS= read -r entry; do
    [ "$path" = "$entry" ] && return 0
    case "$path" in "$entry"/*) return 0 ;; esac
  done < <(sed -n 's/^PUBLISH_PATHS=//p' .promote-target)
  return 1
}
while IFS= read -r -d '' PATHNAME; do
  ships "$PATHNAME" && continue
  git rev-list -1 "refs/tags/$TAG" -- ":(literal)$PATHNAME" | grep -q . && {
    echo "refusing: withheld path still readable in history: $PATHNAME" >&2; exit 1; }
done < <(git ls-tree -r -z --name-only "refs/tags/$TAG")
```

Two details that are load-bearing rather than style. `":(literal)$PATHNAME"`, for
the reason the filter itself uses it: a pathname holding `[`, `*`, or `?` read as a
glob asks about a different path. And `case "$path" in "$entry"/*)` with `$entry`
**quoted**, so an entry naming a directory called `we[i]rd` is compared literally
rather than as a character class.

Be clear about what that costs before installing it: in a repository of any age
it refuses **every** promotion, because a withheld path's history is exactly what
a tag's ancestry carries — and the promotion itself pushes none of that ancestry,
so the refusal protects nothing the push sends. The recursive form also runs
one `git rev-list` per blob in the tree rather than one per top-level entry, which
in a large repository is slow enough to notice — irrelevant in practice, since the
check refuses on the first withheld path it reaches, and unfixable without
reimplementing the filter's own descent inside a hook.

## 5. The content scan → `needs:`

**What it checked.** The tag annotation body, the tag object's `tagger` line, and
the public release body, against five pattern classes, refusing on a finding and
never redacting.

**Why it is not in the base.** Content policy, and the patterns are one
organisation's. It also **never opened a file in the tree** — it read only those
three artifacts — so it never stopped an internal string inside a shipped file
from publishing. That hole was never closed.

**The replacement is a job dependency**, not the hook: a scan belongs where the
pipeline's scanning tooling, artifacts, and reporting already are, and where it
can see the tree rather than three strings.

```yaml
public:promote:
  needs: [{ job: secret-detection }]
```

If the job is contributed by an included component, `optional: true` is
mandatory — omitting it makes the pipeline **invalid** in any pipeline lacking
that component, so the failure is every job refusing to start:

```yaml
  needs: [{ job: ash-sast, optional: true }]
```

`references/content-patterns.md` has the five pattern classes as a starting set
for a repository writing its own scan.

## 6. The two acknowledgements → `needs:` for approval, the hook for the rest

**What they checked.** `ACK_HISTORY_EXPOSURE`, required when the probe found
withheld content readable in history; and `ACK_CONTENT_EXPOSURE`, required when
`PUBLISHER_IDENTITY` had been overridden away from the neutral default. Each was
an environment variable that had to equal the tag.

**Why they are not in the base.** An acknowledgement is a **human decision
recorded as a variable**, which is the weakest available form of it: it travels in
the same environment as the confirmation, it is set once and pasted thereafter,
and a second variable equal to the tag adds no authority the confirmation did not
already carry. The base has exactly one such value, `CONFIRM_SHA`, so there is no
question about which one authorizes a push.

**The replacement, split by what the acknowledgement actually is:**

- **A human saying yes** is an approval. That is `needs:` on a manual job, or the
  forge's own protected-environment approval — a named person and an audit trail,
  rather than a string in a job variable.
- **A machine-checkable precondition** — "the publisher identity is the neutral
  default", "no withheld path is readable in history" — is the hook, where it can
  be re-derived on every run instead of acknowledged once:

```sh
IDENT="$(sed -n 's/^PUBLISHER_IDENTITY=//p' .promote-target | head -1)"
[ "$IDENT" = "release-bot@example.invalid" ] || {
  echo "refusing: non-neutral publisher identity: $IDENT" >&2; exit 1; }
```

The distinction is the same one the table at the top draws, and it is the reason
neither acknowledgement comes back as a variable.

## 7. An unresolved reference out of a published file → the gate hook

**What it would check.** That no file the promotion publishes references a path it
withholds. The common case is a relative Markdown link between documentation
pages: publishing `docs/guides` and withholding `docs/internal` leaves
`[design notes](../internal/notes.md)` resolving internally and broken in the
public tree. A symlink whose target is withheld is the same fault in a different
spelling, and it is worse — the link survives as a dangling entry in the published
tree rather than as a 404 on a page.

**Why it is not in the base.** The base cannot know which references matter. A
Markdown link, an `#include`, an `img src`, a config path, and a prose mention of a
filename are all "references", and which of them is a defect is the installing
repository's policy — the same reason the content scan is not in the base. Refusing
on one would encode a policy nobody stated, and **rewriting** a file would be
worse: the promotion would publish something no commit in the internal repository
contains.

So the promote path proceeds, and the published tree carries the unresolved
reference. That is a deliberate consequence of the allowlist binding at every
depth, not an oversight — `references/mirror-scope.md` states it where the
allowlist itself is explained.

**The replacement.** In `scripts/promote-gates.sh`, against the tag rather than the
worktree, because the hook runs before the filtered tree exists:

```sh
# Collapse '.' and '..' TEXTUALLY. Never with `cd`: that resolves against the
# filesystem, so it would answer about the checkout the hook happens to run in
# rather than about the tree at the tag — and in a bare clone it answers nothing.
normalize() {
  local part out="" IFS=/
  for part in $1; do
    case "$part" in
      ''|.) continue ;;
      ..)   out="${out%/*}" ;;
      *)    out="$out/$part" ;;
    esac
  done
  printf '%s\n' "${out#/}"
}

# Relative Markdown links out of every published Markdown file, resolved against
# the linking file's own directory, and refused when the target does not ship.
# `ships()` is the function from §4 — an entry itself, or any ancestor of it.
#
# FINDINGS ARE COLLECTED AND REFUSED AFTER THE LOOP, and both loops are fed by
# process substitution rather than a pipe. On the right-hand side of a pipe the
# loop body runs in a subshell, where `exit 1` ends the subshell and the hook
# carries on to report success.
BROKEN=""
while IFS= read -r -d '' DOC; do
  case "$DOC" in *.md) ;; *) continue ;; esac
  ships "$DOC" || continue
  while IFS= read -r LINK; do
    case "$LINK" in ''|/*|'#'*|*://*) continue ;; esac   # absolute, anchor, external
    TARGET="$(normalize "$(dirname "$DOC")/$LINK")"
    ships "$TARGET" || BROKEN="$BROKEN
  $DOC -> $TARGET"
  done < <(git cat-file blob "refs/tags/$TAG:$DOC" | grep -oE '\]\([^)#?]+' | cut -c3-)
done < <(git ls-tree -r -z --name-only "refs/tags/$TAG")
[ -z "$BROKEN" ] || {
  echo "refusing: published file(s) reference withheld paths:$BROKEN" >&2; exit 1; }
```

What it does not catch, so that its scope is not mistaken for completeness: a
reference in any syntax other than a Markdown inline link, a link carrying a URL
fragment or query it strips, and a path that ships as a *directory* while the link
names a file inside it that does not — `ships()` answers about the allowlist, and
the allowlist names directories.

The symlink case is a separate query and a much shorter one — mode `120000` in the
tag's tree, with the link target read as the blob's content:

```sh
git ls-tree -r "refs/tags/$TAG" | awk '$1 == "120000" { print $4 }'
```
