#!/usr/bin/env bash
# Promote one internal tag's filtered tree to a public target.
#
# Invoked by its own path, which is not fixed — this script resolves the
# repository root itself and may live anywhere inside it:
#
#   <this-script> [TAG]                      # dry run — reports, pushes nothing
#   CONFIRM_TAG=v0.4.0 <this-script> v0.4.0  # promotes
#
# A dry run prints the exact confirming command for wherever it was invoked from,
# so there is no path here to keep in sync.
#
# TAG defaults to the newest strict-semver tag on origin. Three refusals, all
# before the worktree exists: the configuration is absent, CONFIRM_TAG does not
# equal the tag, or PUBLISH_PATHS does not describe the tag's tree. That last one
# has four forms — an absent path, an ancestor component that is a file, an entry
# an ancestor entry already ships, and a malformed entry — and they are ONE
# refusal, because they are four answers to one question. The tag must also exist
# on origin as an annotated tag — a precondition, not a policy, and what keeps a
# never-pushed bootstrap tag unpublishable. A confirmed run also needs the target
# to be readable, because the public commit is built on the target's own tip.
#
# NO INTERNAL HISTORY IS PUBLISHED. The public commit carries the filtered tree,
# the publisher identity, and a message naming the tag, and its only parent is a
# commit the target already holds, or none. See "the parent" below.
#
# PUBLISH_PATHS ENTRIES MAY BE NESTED, at any depth, naming a directory or a
# file. A directory no entry names but some entry reaches into is published
# PARTIALLY: the named descendants ship and every unnamed sibling is withheld by
# the same absence that withholds an unnamed top-level path. The allowlist
# property is not weaker below the first level — which is why the report names
# what each descended level left behind.
#
# THIS IS A BASE. Every other check is the installing repository's policy and goes
# in scripts/promote-gates.sh; references/promote-extensions.md gives the shape of
# each one omitted here, and the reasoning behind the choices below. Nothing here
# is a stub to fill in.
#
# AN ABSENT CONFIRMATION IS THE DRY RUN, and there is no --dry-run flag: a flag
# that can be passed makes the confirmation unreachable. CONFIRM_TAG is read from
# the ENVIRONMENT only and .promote-target is PARSED, never sourced, so neither
# it nor the gate hook can authorize a push.
set -euo pipefail
export GIT_TERMINAL_PROMPT=0   # no prompt may block a job or wait on a terminal
PUBLIC_BRANCH="main"
PUBLIC_REMOTE="promote-public"   # left configured deliberately — see the push
REPO_ROOT="$(git rev-parse --show-toplevel)"
# Derived, never hardcoded: the only command this script prints for an operator to
# copy is the one that promotes, and a wrong path there is the one papercut
# guaranteed to be hit. Installed at scripts/promote.sh this reports
# `scripts/promote.sh`; moved anywhere else inside the repository it reports where
# it actually is. Resolved BEFORE the cd, since a relative invocation is relative
# to the caller's directory.
#
# `pwd -P` ON BOTH SIDES is load-bearing, and it is the whole reason the root is
# resolved a second time here rather than the strip using $REPO_ROOT directly.
# `git rev-parse --show-toplevel` returns a PHYSICAL path while `pwd` returns the
# logical one, so on any tree reached through a symlinked ancestor the two
# disagree, the prefix fails to match, and the report prints a correct but
# absolute path instead of a repo-relative one. macOS makes this the common case,
# not the exotic one: /tmp and /var are symlinks to /private/tmp and /private/var,
# so every run under mktemp -d hits it. Measured — this printed
# /var/folders/.../scripts/promote.sh before the -P was added.
#
# If the strip still does not match, SELF_REL stays absolute. That is a correct
# runnable command, merely a verbose one, so there is no failure path here.
SELF_REL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
SELF_REL="${SELF_REL#"$(cd "$REPO_ROOT" && pwd -P)"/}"
cd "$REPO_ROOT"
CONFIG_FILE="$REPO_ROOT/.promote-target"
GATE_HOOK="$REPO_ROOT/scripts/promote-gates.sh"

# Exact string membership — never a glob, never a substring, so a path containing
# a space, '[', '*', or '?' compares as written, at any depth.
contains() {
  local needle="$1" item; shift
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}
# True when some allowlist entry lies STRICTLY beneath "$1" — the test that tells
# a directory to descend into from one to remove whole. The "$1" is quoted inside
# the case pattern so it is matched literally: unquoted, a directory named
# 'we[i]rd' would be read as a character class and match nothing.
reaches_into() {
  local path="$1" entry
  for entry in ${PUBLISH_PATHS[@]+"${PUBLISH_PATHS[@]}"}; do
    case "$entry" in "$path"/*) return 0 ;; esac
  done
  return 1
}
die() { printf 'error: %s\n' "$1" >&2; shift; [ $# -eq 0 ] || printf 'hint: %s\n' "$@" >&2; exit 1; }

# --- refusal 1: configuration absent -------------------------------------
[ -f "$CONFIG_FILE" ] || die "no promote configuration at $CONFIG_FILE" \
  "copy assets/promote-target.template there and fill in all three keys"
# A value is LITERAL — quotes are part of it, so PUBLISH_PATHS="skills" names a
# path including the quotes and refusal 2 says so. One line per path: newline is
# the only separator a path cannot hold.
PUBLIC_TARGET=""
PUBLISHER_IDENTITY=""
PUBLISH_PATHS=()
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  case "$line" in *=*) ;; *) continue ;; esac
  case "${line%%=*}" in
    PUBLIC_TARGET) PUBLIC_TARGET="${line#*=}" ;;
    PUBLISHER_IDENTITY) PUBLISHER_IDENTITY="${line#*=}" ;;
    PUBLISH_PATHS) PUBLISH_PATHS+=("${line#*=}") ;;
    CONFIRM_TAG|DRY_RUN)
      echo "note: ${line%%=*} here is ignored — the confirmation is read from the" >&2
      echo "      environment only, so this file cannot authorize a push" >&2 ;;
  esac
done < "$CONFIG_FILE"
for key in PUBLIC_TARGET PUBLISHER_IDENTITY; do
  [ -n "${!key}" ] || die "$CONFIG_FILE declares no $key"
done
[ "${#PUBLISH_PATHS[@]}" -gt 0 ] || die "$CONFIG_FILE declares no PUBLISH_PATHS"

# --- refusal 2, first form: an entry whose SHAPE is not a path -----------
# A shape fault needs no tree to see, so it is caught here rather than against the
# tag. That is observable, not tidiness: the same refusal then arrives whether the
# tag was named or derived, and a repository with no tag at all still gets the real
# reason instead of "origin carries no strict-semver tag".
#
# An entry names a path relative to the repository root. A leading separator would
# read as absolute, a trailing one or an empty component as a typo, and '.' or '..'
# as a traversal an allowlist has no business expressing. One reason per entry: the
# first matching form is the one reported.
malformed=()
for want in "${PUBLISH_PATHS[@]}"; do
  case "$want" in
    '')                  malformed+=("'$want' — an empty entry") ;;
    /*)                  malformed+=("'$want' — a leading separator") ;;
    */)                  malformed+=("'$want' — a trailing separator") ;;
    *//*)                malformed+=("'$want' — an empty component") ;;
    ..|../*|*/../*|*/..) malformed+=("'$want' — a .. component") ;;
    .|./*|*/./*|*/.)     malformed+=("'$want' — a . component") ;;
  esac
done
if [ "${#malformed[@]}" -gt 0 ]; then
  echo "error: $CONFIG_FILE names ${#malformed[@]} unusable PUBLISH_PATHS entry(s):" >&2
  printf '  %s\n' "${malformed[@]}" >&2
  echo "hint: an entry names a path relative to the repository root, at any depth —" >&2
  echo "      no leading or trailing separator, no empty component, and no '.' or" >&2
  echo "      '..' component. A fault in an entry's shape needs no tree to see, so" >&2
  echo "      it refuses before any tag is resolved." >&2
  exit 1
fi

# --- the tag -------------------------------------------------------------
TAG="${1:-}"
case "$TAG" in
  -*) die "unknown flag: $TAG — this script takes no flags" \
        "omitting CONFIRM_TAG is what makes a run a dry run" ;;
esac
if [ -z "$TAG" ]; then
  # sort -V, not sort: plain sort ranks v0.1.2 above v0.1.10.
  TAG="$(git ls-remote --tags --refs origin 2>/dev/null \
    | awk '{ sub(/^refs\/tags\//, "", $2); print $2 }' \
    | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1 || true)"
  [ -n "$TAG" ] || die "origin carries no strict-semver tag"
fi
# Absent from origin is not an internal release; lightweight has no annotation.
[ -n "$(git ls-remote --tags --refs origin "refs/tags/$TAG" 2>/dev/null)" ] || \
  die "$TAG is not a tag on origin" \
    "a local-only tag — a bootstrap tag, say — is not an internal release"
[ "$(git cat-file -t "refs/tags/$TAG" 2>/dev/null || true)" = "tag" ] || \
  die "$TAG is not an annotated tag in this clone" \
    "git fetch origin --tags — the promotion reuses the annotation"

# --- refusal 2, remaining forms: the allowlist vs the tag's tree ---------
# A count of entries is no substitute for any of this: it passes against an entry
# naming a path that does not exist, which is the case that ships a wrong tree.
#
# `git rev-parse --verify --quiet "<tag>:<path>"` is the existence test.
# `git ls-tree -- <path>` cannot be — it exits 0 with EMPTY OUTPUT for an absent
# path (measured). rev-parse also interprets no glob character, so 'we[i]rd/sub'
# resolves as written and needs none of the ':(literal)' care a pathspec does.
faults=()
for want in "${PUBLISH_PATHS[@]}"; do
  # An entry an ancestor entry already ships whole is dead configuration that
  # reads as a narrowing in effect. It REFUSES rather than warns: a warning lands
  # in a report nobody rereads, and deleting the ancestor line later — reasonably,
  # believing the specific line governs — would then narrow what ships silently.
  shadow=""
  for other in "${PUBLISH_PATHS[@]}"; do
    [ "$other" = "$want" ] && continue
    case "$want" in "$other"/*) shadow="$other"; break ;; esac
  done
  if [ -n "$shadow" ]; then
    faults+=("'$want' — '$shadow' already ships it")
    continue
  fi
  # Every STRICT ancestor component must be a tree, checked shallowest first and
  # BEFORE the entry itself, so the message names the component that cannot be
  # descended into rather than reporting a correctly-spelled path as a typo.
  fault=""
  prefix=""
  rest="$want"
  while [ "$rest" != "${rest#*/}" ]; do
    prefix="$prefix${rest%%/*}"
    rest="${rest#*/}"
    kind="$(git cat-file -t "refs/tags/$TAG:$prefix" 2>/dev/null || true)"
    if [ -z "$kind" ]; then
      fault="no such path at the tag"
      break
    elif [ "$kind" != "tree" ]; then
      fault="'$prefix' is not a directory"
      break
    fi
    prefix="$prefix/"
  done
  if [ -z "$fault" ]; then
    git rev-parse --verify --quiet "refs/tags/$TAG:$want" >/dev/null 2>&1 || \
      fault="no such path at the tag"
  fi
  [ -z "$fault" ] || faults+=("'$want' — $fault")
done
if [ "${#faults[@]}" -gt 0 ]; then
  echo "error: $CONFIG_FILE names ${#faults[@]} PUBLISH_PATHS entry(s) the tree at $TAG does not describe:" >&2
  printf '  %s\n' "${faults[@]}" >&2
  echo "hint: a misspelling, a path that has moved, or two entries merged onto one" >&2
  echo "      line. If it is deliberately gone, delete its PUBLISH_PATHS line — the" >&2
  echo "      allowlist names what ships, so that withholds nothing. If an ancestor" >&2
  echo "      entry already ships it, the narrowing the entry implies is not in" >&2
  echo "      effect: delete one of the two lines, whichever states what you mean." >&2
  exit 1
fi

# --- the traversal: ONE descent feeds both the report and the push -------
# Per child of every visited directory, EXACTLY ONE of three things: a child that
# is an allowlist entry is kept whole and not descended into, a child some entry
# reaches into is descended into, and anything else is removed. Total and mutually
# exclusive, which is what makes the result auditable — every child of every
# visited directory lands in exactly one bucket.
#
# IT READS THE TAG'S TREE AND NEVER A WORKTREE, because the dry run exits before
# one exists. That constraint buys the design's best property: the report and the
# push come from one computation, so the `git rm` loop further down is the
# execution of a decision already made and already printed, rather than a second
# place the decision gets made.
#
# A worklist rather than recursion, and `contains()`'s linear scan rather than a
# hash set: bash 3.2 has no associative arrays and macOS ships it as /bin/bash.
# Linear is fine at the size of a repository's directory listing.
#
# The record form is the PORTABLE one — `<mode> SP <type> SP <oid> TAB <name>`,
# NUL-terminated under -z, so a name holding a space or a newline is read as
# written. `git ls-tree --format=` is the readable spelling and needs git >= 2.36:
# this file is installed into repositories whose git version it cannot see.
# `<tree-ish>:<path>` is what makes the descent safe — it resolves a path
# literally, with no pathspec globbing, so 'we[i]rd' descends correctly.
QUEUE=("")        # "" is the root tree; every other entry is a directory path
KEPT=()           # what ships, in tree order
REMOVE=()         # what is removed, each named at the shallowest level it can be
REPORT=()         # the per-level withheld blocks, in the order descended
qi=0
while [ "$qi" -lt "${#QUEUE[@]}" ]; do
  dir="${QUEUE[$qi]}"
  qi=$((qi + 1))
  level=()
  children=0
  while IFS= read -r -d '' record; do
    children=$((children + 1))
    name="${record#*$'\t'}"
    kind="${record#* }"; kind="${kind%% *}"
    if [ -n "$dir" ]; then path="$dir/$name"; else path="$name"; fi
    if contains "$path" "${PUBLISH_PATHS[@]}"; then
      KEPT+=("$path")
    elif reaches_into "$path"; then
      # Only a tree can be descended into, and entry validation above already
      # proved every ancestor component of every entry is one. So this is an
      # assertion that the two agree, not a policy: reaching it would mean the
      # traversal was about to remove a path the allowlist publishes.
      [ "$kind" = "tree" ] || \
        die "internal: $path is a $kind, but the allowlist names something beneath it"
      QUEUE+=("$path")
    else
      REMOVE+=("$path")
      level+=("$path")
    fi
  done < <(git ls-tree -z "refs/tags/$TAG:$dir")
  [ -n "$dir" ] || [ "$children" -gt 0 ] || die "the tree at $TAG has no top-level entries"
  # A level contributes a withheld block only when it left something behind. A
  # directory shipped whole is never visited, so it is never expanded.
  if [ "${#level[@]}" -gt 0 ]; then
    if [ -n "$dir" ]; then REPORT+=("withheld under $dir:"); else REPORT+=("withheld:"); fi
    for path in "${level[@]}"; do
      REPORT+=("  $path")
    done
  fi
done
# Every entry is reached exactly once: validation proved each one resolves at the
# tag, and the descent visits every strict ancestor of every entry. A mismatch
# means validation and traversal disagree about the tree, which would publish or
# withhold something nobody named. An invariant, not a refusal — it encodes no
# policy and there is no configuration that reaches it.
#
# DISTINCT entries, not raw lines. A duplicated PUBLISH_PATHS line is dead but
# harmless: it names exactly what already ships, so it is none of the four ways an
# allowlist fails to describe the tree, and it must promote. The traversal keeps
# that path once, so counting raw lines here would report an operator's duplicated
# line as an internal inconsistency — the one shape of this check that could fire
# on a real configuration.
DISTINCT=()
for want in "${PUBLISH_PATHS[@]}"; do
  contains "$want" ${DISTINCT[@]+"${DISTINCT[@]}"} || DISTINCT+=("$want")
done
[ "${#KEPT[@]}" -eq "${#DISTINCT[@]}" ] || \
  die "internal: the traversal kept ${#KEPT[@]} of ${#DISTINCT[@]} declared path(s)"
if [ -x "$GATE_HOOK" ]; then
  HOOK_STATE="present"
elif [ -e "$GATE_HOOK" ]; then
  HOOK_STATE="PRESENT BUT NOT EXECUTABLE — it will NOT run (chmod +x it, or remove it)"
else
  HOOK_STATE="not present"
fi

# --- the parent: what the public commit is built on ----------------------
# Decided here, before the report, and printed with it, so the dry run and the
# push read one answer. Three sources, in order:
#
#   1. a remote-tracking ref for the target — the record of what THIS CLONE last
#      promoted. Only a push to the named remote writes it; nothing here fetches
#      into it. The lease stays bare and expects exactly that record.
#   2. the target's current tip, when the clone holds no record — ADOPTED as the
#      parent, with a lease naming exactly that tip. This is what the first
#      promotion to a target holding an initial commit needs; a bare lease with no
#      record expects no branch at all and is refused with `stale info`.
#   3. no branch on the target — a root commit, and a bare lease expecting none.
#
# A FRESH CLONE HAS NO RECORD, SO EVERY CI RUN TAKES SOURCE 2. There the lease
# guards only the interval between this read and the push: a commit someone else
# put on the target becomes the parent rather than a refusal, and the promoted
# tree replaces its content. The dry run names it. A repository that wants that
# refused adds the divergence gate in references/promote-extensions.md.
#
# READ-ONLY ON EVERY PATH, because the dry run exits after the report: a local ref,
# or ls-remote against the URL, which configures no remote and fetches nothing. An
# unreadable target — a private one, read by a job holding no credential, which is
# every CI dry run — is reported here, and only a confirmed run fails on it.
PARENT=""
ADOPT=""
UNREADABLE=""
LEASE="--force-with-lease"
if [ "$(git remote get-url "$PUBLIC_REMOTE" 2>/dev/null || true)" = "$PUBLIC_TARGET" ] &&
   PARENT="$(git rev-parse --verify --quiet "refs/remotes/$PUBLIC_REMOTE/$PUBLIC_BRANCH^{commit}")"; then
  PARENT_REPORT="$PARENT — the commit this clone last promoted"
elif TIP="$(git ls-remote "$PUBLIC_TARGET" "refs/heads/$PUBLIC_BRANCH" 2>/dev/null)"; then
  # ls-remote matches a pattern against the END of each ref name; compare exactly.
  PARENT="$(printf '%s\n' "$TIP" | awk -v ref="refs/heads/$PUBLIC_BRANCH" '$2 == ref { print $1 }')"
  if [ -n "$PARENT" ]; then
    ADOPT="yes"
    LEASE="--force-with-lease=refs/heads/$PUBLIC_BRANCH:$PARENT"
    PARENT_REPORT="$PARENT — the target's current tip, adopted: this clone holds no record of a promotion to it"
  else
    PARENT_REPORT="none — the target has no $PUBLIC_BRANCH branch, so the public commit is a root commit"
  fi
else
  UNREADABLE="yes"
  PARENT_REPORT="unknown — the target could not be read (a private target cannot be read without a credential)"
fi

# --- the report, printed on every run ------------------------------------
echo "tag:        $TAG"
echo "target:     $PUBLIC_TARGET"
echo "parent:     $PARENT_REPORT"
echo "history:    not published — the public commit carries the filtered tree and no internal commit"
# Both halves come from the traversal, not from the configuration, so the report
# describes the tree that is about to be pushed rather than the list that was
# declared. A PARTIALLY PUBLISHED DIRECTORY IS WHERE THIS ALLOWLIST'S ACCEPTED
# FAILURE MODE HIDES: a new page added beside the published ones silently does not
# ship. The per-level block is what keeps that failure quiet rather than silent —
# a builder who forgot an allowlist line reads it here, on the next dry run,
# instead of discovering it as a missing page in the public tree.
echo "ships:"
printf '  %s\n' "${KEPT[@]}"
if [ "${#REPORT[@]}" -gt 0 ]; then
  printf '%s\n' "${REPORT[@]}"
else
  echo "withheld:   nothing — the allowlist names every path in the tree at $TAG"
fi
echo "repo gates: $HOOK_STATE"

# --- refusal 3: the confirmation must equal the tag ----------------------
if [ -z "${CONFIRM_TAG:-}" ]; then
  echo "dry run: nothing was pushed."
  echo "to promote: CONFIRM_TAG=$TAG $SELF_REL $TAG"
  exit 0
fi
[ "$CONFIRM_TAG" = "$TAG" ] || \
  die "CONFIRM_TAG is '$CONFIRM_TAG' but the tag being promoted is '$TAG'" \
    "a prepared command whose tag moved under it fails closed here"
# A precondition, like the tag being on origin, and not a fourth refusal: with no
# readable target there is nothing to build on, and the push would fail the same
# way, only later.
[ -z "$UNREADABLE" ] || die "cannot read $PUBLIC_TARGET — nothing pushed" \
  "a private target needs a credential wherever the confirmed promotion runs"
# Executed, never sourced: a subshell, TAG and PUBLIC_TARGET exported, exit status
# only — it cannot set the confirmation or cause a push. Absent is not an error.
if [ -x "$GATE_HOOK" ]; then
  TAG="$TAG" PUBLIC_TARGET="$PUBLIC_TARGET" "$GATE_HOOK" || \
    die "scripts/promote-gates.sh refused the promotion — nothing pushed"
elif [ -e "$GATE_HOOK" ]; then
  echo "warning: $GATE_HOOK is not executable and did not run" >&2
fi

# --- filter, commit, retag, push ----------------------------------------
WORKTREE_DIR="$(mktemp -d)/promote"
cleanup() { [ -d "$WORKTREE_DIR" ] && git worktree remove "$WORKTREE_DIR" 2>/dev/null || true; }
trap cleanup EXIT
git worktree add --quiet --detach "$WORKTREE_DIR" "refs/tags/$TAG"
# ':(literal)' is load-bearing: git reads a pathspec as a glob, so a name holding
# '[', '*', or '?' would match something else, or nothing, and be silently kept.
# The ${arr[@]+…} guard is too: a bare "${REMOVE[@]}" on an EMPTY array aborts
# under `set -u` in bash before 4.4, and macOS ships 3.2 as /bin/bash. Measured.
#
# REMOVALS STAY SHALLOW. The traversal names a withheld path at the shallowest
# level it can, so this loop keeps its shape and roughly its invocation count now
# that entries may nest — a removal set enumerated file by file would be unreadable
# in a diff or a log and would multiply invocations by orders of magnitude. A
# directory this loop descends past is never emptied by it: the traversal descends
# into a directory only because some entry ships beneath it.
for path in ${REMOVE[@]+"${REMOVE[@]}"}; do
  git -C "$WORKTREE_DIR" rm -rq -- ":(literal)$path"
done
# An adopted tip is fetched only now, because commit-tree needs the parent object.
# By id, so the commit built on is the one the report named and the lease expects;
# and into no ref, so the record above stays something only a push writes.
[ -z "$ADOPT" ] || git fetch --quiet --no-tags "$PUBLIC_TARGET" "$PARENT"
# commit-tree, NOT commit --amend. An amended commit keeps its parents, so its push
# sent every earlier internal commit too: each withheld path at each past revision,
# each internal subject, each author address. commit-tree writes one object from
# the filtered tree and moves no ref, the property mktag gives the tag below.
#
# Identity from the environment, which outranks both git config and an inherited
# GIT_AUTHOR_*. Both dates are the tag's tagger date, so one tag promoted onto one
# parent always builds the same commit. The message names the tag and nothing
# else; the notes stay in the annotation. commit-tree runs no hooks, and
# gpgsign=false keeps a configured signing key from failing a publish at its
# latest possible moment.
TREE="$(git -C "$WORKTREE_DIR" write-tree)"
TAGGER_DATE="$(git for-each-ref --format='%(taggerdate:raw)' "refs/tags/$TAG")"
PUBLIC_COMMIT="$(
  GIT_AUTHOR_NAME=promote GIT_AUTHOR_EMAIL="$PUBLISHER_IDENTITY" GIT_AUTHOR_DATE="$TAGGER_DATE" \
  GIT_COMMITTER_NAME=promote GIT_COMMITTER_EMAIL="$PUBLISHER_IDENTITY" GIT_COMMITTER_DATE="$TAGGER_DATE" \
  git -c commit.gpgsign=false commit-tree "$TREE" ${PARENT:+-p "$PARENT"} -m "Promote $TAG"
)"
# The annotation is reused byte for byte, nothing asserted about its content, so
# a hand-cut tag promotes. git mktag writes an object and no ref: a worktree
# shares refs/tags with its parent, so `git tag -f` would move the OPERATOR's tag.
ANNOTATION="$(git cat-file tag "refs/tags/$TAG" | sed '1,/^$/d')"
TAG_OBJECT="$(
  {
    echo "object $PUBLIC_COMMIT"
    echo "type commit"
    echo "tag $TAG"
    echo "tagger promote <$PUBLISHER_IDENTITY> $TAGGER_DATE"
    echo
    printf '%s\n' "$ANNOTATION"
  } | git mktag
)"
# A configured remote, LEFT in place: the push writes its remote-tracking ref, and
# that ref is the record "the parent" reads first on the next run from this clone.
# The lease expects the tip the public commit was built on — the record, the
# adopted tip, or no branch — so any other public tip refuses the push rather than
# being overwritten. That is the base's floor in place of a divergence gate.
if [ "$(git remote get-url "$PUBLIC_REMOTE" 2>/dev/null || true)" != "$PUBLIC_TARGET" ]; then
  git remote remove "$PUBLIC_REMOTE" 2>/dev/null || true
  git remote add "$PUBLIC_REMOTE" "$PUBLIC_TARGET"
fi
# --atomic: branch and tag land together or neither does. No fallback.
git push --quiet --atomic "$LEASE" "$PUBLIC_REMOTE" \
  "$PUBLIC_COMMIT:refs/heads/$PUBLIC_BRANCH" "$TAG_OBJECT:refs/tags/$TAG"
echo "promoted $TAG to $PUBLIC_TARGET (${#KEPT[@]} path(s))"
