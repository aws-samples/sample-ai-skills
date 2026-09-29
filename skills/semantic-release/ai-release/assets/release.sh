#!/usr/bin/env bash
# Cut an internal release: tag origin and create a GitLab Release.
#
# Usage: scripts/release.sh
#
#   Takes NO arguments. The version is DERIVED from tags and Conventional Commit
#   history — there is no VERSION file and no way to request a version. That is
#   deliberate: a requestable version is a version somebody gets wrong.
#
# Environment:
#   PREVIEW=1         print what would be released and exit 0. Creates nothing,
#                     and needs no network.
#   CONFIRM_VERSION   required, equal to the derived tag, when the release
#                     raises the MAJOR version.
#
# Runs identically in CI (the gitlab:release job) and from a workstation, which
# is what makes a release possible when CI is unavailable.
#
# Cutting an internal release publishes NOTHING publicly. Publishing to a public
# remote is a separate, deliberate act — see the release how-to.
#
# ---------------------------------------------------------------------------
# THE ORDERING IS THE DESIGN. Do not reorder these steps.
# ---------------------------------------------------------------------------
#
#   0. Tagless refusal.       Before derivation, because derivation is what fails.
#   1. Derive.                Everything below is a statement about this value.
#   2. Preview, exit 0.       First, because everything below touches the network.
#   3. No-op, exit 0.         "Nothing to release" is an answer, not a failure —
#                             but only once origin confirms the tag was pushed.
#   4. Major guard.           Refuse before spending work on notes.
#   5. Tag hygiene.           A disagreeing tag means derivation read the wrong base.
#   6. Tag absence.           The double-tag guard.
#   7. Notes + heading assert.
#   8. Tag, push, Release object.
#
# Steps 4-7 all run BEFORE the tag exists, because a gate that fires after
# tagging is not a gate — the tag would already be on origin by the time it
# complained.

set -euo pipefail

# This script's own directory. Every hint below and the forge probe near the end
# are built from it rather than from a hardcoded `scripts/`, because the pair is
# installed into `scripts/` in a consumer repository and lives under
# `internal/scripts/` in the repository that ships this template. One
# byte-identical file has to be right in both, and a hint naming a path that does
# not exist sends a maintainer looking for a missing file.
self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -gt 0 ]; then
  echo "error: release.sh takes no arguments (got: $*)" >&2
  echo "hint: the version is derived from commit history, not supplied. To" >&2
  echo "      preview, run: PREVIEW=1 bash $0" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 0. Tagless refusal
# ---------------------------------------------------------------------------
#
# Derivation cannot bootstrap itself: on a repository with no tags,
# `git-cliff --bumped-version` exits 1 with "Next version (0.1.0) does not
# match the tag pattern", because its no-release fallback emits a bare `0.1.0`
# while `tag_pattern` requires a leading `v`. Failing to derive means no tag is
# created, so there is still nothing to derive from next time.
#
# That raw error names nothing about the cause, so refuse in terms of the
# actual state and print the one-time action. The bootstrap version is NOT
# inferred: where the tag sits decides which commits the first derived release
# describes, so it is a choice an operator makes rather than one a script makes
# for them.

if [ -z "$(git tag --list)" ]; then
  ROOT=$(git rev-list --max-parents=0 HEAD)
  echo "error: this repository has no tags, so no version can be derived" >&2
  echo "hint: version derivation walks back to the newest release tag. With" >&2
  echo "      none, there is no base to derive from, and creating one is a" >&2
  echo "      one-time bootstrap an operator performs deliberately:" >&2
  echo "        git tag -a v0.1.0 --cleanup=verbatim -F <annotation-file> $ROOT" >&2
  echo "        git push origin v0.1.0" >&2
  echo "hint: the commit you tag decides which commits the FIRST derived" >&2
  echo "      release describes — tagging the root commit puts all of history" >&2
  echo "      inside it. --cleanup=verbatim is mandatory: the default cleanup" >&2
  echo "      mode strips every '#'-leading line — every Markdown heading —" >&2
  echo "      and exits 0 doing it. See the release how-to. Nothing" >&2
  echo "      was created." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Derive
# ---------------------------------------------------------------------------

TAG=$(git-cliff --bumped-version)
LATEST=$(git describe --tags --abbrev=0 --match='v[0-9]*.[0-9]*.[0-9]*' 2>/dev/null || echo "none")

# ---------------------------------------------------------------------------
# 2. Preview
# ---------------------------------------------------------------------------
#
# One script, one early return, rather than a separate preview path — so the
# preview cannot report notes that differ from what a release publishes.
#
# FIRST, before every other check, because none of the others are
# network-free: even the no-op below asks origin whether the newest tag was
# pushed. A preview that requires the network is a preview that fails on a
# plane. The cost is that a preview does not detect a poisoned clone —
# acceptable, because it creates nothing and the release path still refuses.

if [ "${PREVIEW:-}" = "1" ]; then
  echo "current release: $LATEST"
  echo "would release:   $TAG"

  if [ "$TAG" = "$LATEST" ]; then
    echo ""
    echo "Nothing to release — no commits since $LATEST affect the version."
    echo "Only conventional commits (feat:, fix:, ...) derive a new version."
    exit 0
  fi

  echo ""
  echo "--- release notes for $TAG ---"
  git-cliff --unreleased --tag "$TAG" --strip all
  echo "--- end release notes ---"
  echo ""
  echo "Nothing was created. To cut this release, run the 'gitlab:release' job."
  exit 0
fi

# ---------------------------------------------------------------------------
# 3. The idempotent no-op
# ---------------------------------------------------------------------------
#
# Exits 0 DELIBERATELY. The release job is a button that can be clicked
# speculatively, and a red pipeline for "you clicked it and there was nothing
# to do" is a red pipeline everyone learns to ignore — at which point it also
# hides the one time it means something.
#
# But "derived equals newest" has TWO causes, and only one of them is nothing
# to do. If a previous run created the tag locally and then failed to push it,
# `git describe` reports it, derivation reports it back, and this branch would
# say "nothing to release" and exit 0 — leaving a release that never reached
# origin and reporting success for it. So the local tag is confirmed present
# on origin before the no-op is believed. This costs one `git ls-remote`,
# which is why the preview above returns before reaching it.

if [ "$TAG" = "$LATEST" ]; then
  if git ls-remote --tags origin "refs/tags/$LATEST" | grep -q "$LATEST"; then
    echo "Nothing to release — derived version equals the current tag ($LATEST)."
    echo "Only conventional commits (feat:, fix:, ...) derive a new version."
    echo "Nothing was created."
    exit 0
  fi

  echo "error: tag $LATEST exists locally but NOT on origin" >&2
  echo "hint: a previous release run created the tag and failed before" >&2
  echo "      pushing it, so this release was never published." >&2
  echo "hint: push it and create the Release object:" >&2
  echo "        git push origin $LATEST" >&2
  echo "        bash $self_dir/gitlab-release.sh $LATEST <notes-file>" >&2
  echo "hint: or discard it and start over: git tag -d $LATEST" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 4. Major-version guard
# ---------------------------------------------------------------------------
#
# Keyed on the SHAPE of the derived version, not on commit text, so it holds
# before and after 1.0. cliff.toml's `breaking_always_bump_major = false` is
# retained as belt and braces but is INERT once the major reaches 1 — verified:
# at v1.0.0 a `feat!:` still derives v2.0.0. This guard is what survives.
#
# CONFIRM_VERSION must equal the derived tag exactly rather than being a
# boolean, so a stale confirmation fails closed: if history moves between the
# refusal and the retry, the derived version changes and the old value no
# longer matches.
#
# LATEST is read with --match above, so a stray non-release tag cannot become
# the comparison base: without --match, one stray tag makes this comparison
# error with "integer expression expected" inside the `if`, which `set -e`
# does NOT catch (a failure inside an `if` condition is exempt by design), and
# a major bump would proceed unconfirmed.

if [ "$LATEST" != "none" ]; then
  new_major=${TAG#v};    new_major=${new_major%%.*}
  old_major=${LATEST#v}; old_major=${old_major%%.*}

  if [ "$new_major" -gt "$old_major" ] && [ "${CONFIRM_VERSION:-}" != "$TAG" ]; then
    echo "error: this release changes the MAJOR version ($LATEST -> $TAG)" >&2
    echo "hint: re-run with CONFIRM_VERSION=$TAG" >&2
    echo "hint: nothing was created. Read the notes with PREVIEW=1 first if" >&2
    echo "      you did not expect a major bump." >&2
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 5. Tag hygiene
# ---------------------------------------------------------------------------
#
# Every local release tag must point at the same object as origin's tag of the
# same name. A disagreeing tag poisons both computations the release path
# depends on: version derivation reads the wrong base (`git describe` returns
# the previous tag) and any publish range resolves against the wrong commit.
#
# Near-tautological in CI, which fetches --tags --force into a fresh clone. It
# earns its lines locally, where the failure is silent.
check_tag_hygiene() {
  local ref local_sha origin_sha tag disagreements=0

  while IFS=$'\t' read -r origin_sha ref; do
    tag="${ref#refs/tags/}"
    # Peeled entries (refs/tags/<name>^{}) restate the annotated tag's target;
    # comparing the tag object itself is what matters here.
    [ "${tag%^\{\}}" = "$tag" ] || continue

    # A tag that exists on origin but not locally is not a disagreement —
    # there is nothing local to be wrong. Only a name present on BOTH sides
    # can disagree.
    local_sha=$(git rev-parse --verify --quiet "refs/tags/$tag") || continue

    if [ "$local_sha" != "$origin_sha" ]; then
      echo "error: local tag $tag disagrees with origin" >&2
      echo "  local:  $local_sha" >&2
      echo "  origin: $origin_sha" >&2
      disagreements=$((disagreements + 1))
    fi
  done < <(git ls-remote --tags origin | grep -E 'refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$' || true)

  if [ "$disagreements" -gt 0 ]; then
    echo "hint: repair this clone with: git fetch origin --tags --force" >&2
    echo "hint: nothing was created." >&2
    exit 1
  fi

  echo "ok: local release tags agree with origin"
}

check_tag_hygiene

# ---------------------------------------------------------------------------
# 6. Tag absence — the double-tag guard
# ---------------------------------------------------------------------------
#
# Checked on BOTH sides. A local-only tag would make `git tag -a` fail with a
# less informative message; an origin-side tag means the version is already
# released and this run must not proceed.

if git rev-parse --verify --quiet "refs/tags/$TAG" >/dev/null; then
  echo "error: tag $TAG already exists locally" >&2
  echo "hint: if it was created by a failed run, delete it (git tag -d $TAG)" >&2
  echo "      and re-run. If it exists on origin too, $TAG is already released." >&2
  exit 1
fi

if git ls-remote --tags origin "refs/tags/$TAG" | grep -q "$TAG"; then
  echo "error: tag $TAG already exists on origin — nothing to release" >&2
  echo "hint: $TAG has already been released. If the GitLab Release object is" >&2
  echo "      missing but the tag exists, run gitlab-release.sh directly:" >&2
  echo "        bash $self_dir/gitlab-release.sh $TAG <notes-file>" >&2
  exit 1
fi

echo "Releasing $TAG (current: $LATEST)"

# ---------------------------------------------------------------------------
# 7. Notes
# ---------------------------------------------------------------------------
#
# --tag stamps the heading as "## [X.Y.Z] - <date>". Without it the notes are
# headed "## [Unreleased]", which is wrong on a tag that names a version — and
# any publish path that reads this annotation requires a '## [' heading in it.
#
# Generated HERE, from current history. There is no committed changelog to
# read from, and generating fresh is what makes the published notes complete.

git-cliff --unreleased --tag "$TAG" --strip all > /tmp/release-notes.md

# TWO assertions, because the heading alone is not evidence of content.
#
# The heading check protects the contract a consumer reads: the notes become
# both the tag annotation and the GitLab Release description, and a release
# that names a version without a version heading is a release nobody can
# navigate.
if ! grep -q '^## \[' /tmp/release-notes.md; then
  echo "error: generated notes for $TAG contain no version heading" >&2
  echo "hint: a '## [' heading is required in the tag annotation, which" >&2
  echo "      becomes the GitLab Release description verbatim. Refusing to" >&2
  echo "      create a tag whose notes have no version heading. Nothing was" >&2
  echo "      created." >&2
  exit 1
fi

# The content check catches a CONTENTLESS release, which the heading check
# cannot see: `--tag` always stamps the heading, so notes with a heading and
# no entries pass it. That state is reachable, and not exotic —
#
#   a commit matching NO parser at all (a bare "wip", a plain "Add thing", or
#   a "Merge branch ..." commit) derives a PATCH but is grouped into nothing,
#   so it contributes a version bump and zero entries. Verified: a chore-only
#   branch merged with --no-ff derives a patch whose notes are one heading and
#   nothing else.
#
# Only parsers with `skip = true` (^chore, ^style, ^test) suppress the bump;
# everything unmatched still bumps. So refuse rather than publish a release
# that describes nothing.
if ! grep -q '^- ' /tmp/release-notes.md; then
  echo "error: generated notes for $TAG contain a heading but no entries" >&2
  echo "" >&2
  cat /tmp/release-notes.md >&2
  echo "" >&2
  echo "hint: every commit in this window is either skipped (chore:, style:," >&2
  echo "      test:) or matches no conventional type at all. An unmatched" >&2
  echo "      commit — a bare 'wip', a plain 'Add thing', or a merge commit —" >&2
  echo "      still derives a patch bump but is grouped into nothing, which is" >&2
  echo "      how a version can be derivable with nothing to say." >&2
  echo "hint: reword the commits conventionally, or leave the release uncut." >&2
  echo "      Nothing was created." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 7b. Credential pre-flight — BEFORE the tag exists
# ---------------------------------------------------------------------------
#
# Checked here, not left for gitlab-release.sh to discover after step 8 has
# already pushed the tag. A release object can be recreated any time; a
# pushed tag cannot be un-pushed without a force-delete on origin. So the
# forge-release credential is verified while nothing irreversible has
# happened yet, and the workstation path (GITLAB_TOKEN, a personal access
# token) is accepted as an alternative to CI_JOB_TOKEN rather than treated as
# a partial failure.
if [ -z "${CI_JOB_TOKEN:-}" ] && [ -z "${GITLAB_TOKEN:-}" ] && [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "error: no forge credential is set (checked CI_JOB_TOKEN, GITLAB_TOKEN," >&2
  echo "      GITHUB_TOKEN)" >&2
  echo "hint: creating the forge Release object needs one of them. In CI," >&2
  echo "      CI_JOB_TOKEN (GitLab) is issued automatically. From a" >&2
  echo "      workstation, export GITLAB_TOKEN with a personal access token" >&2
  echo "      carrying api scope, then re-run." >&2
  echo "hint: refusing before the tag is created — nothing was created." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 8. Tag, push, publish internally
# ---------------------------------------------------------------------------
#
# `--cleanup=verbatim -F` is LOAD-BEARING, not stylistic. Git's default
# cleanup mode strips #-leading lines as comments and reflows content — and
# EXITS 0 while doing it, so the loss is silent. The notes are Markdown whose
# every section heading starts with `#`, so the default would reduce grouped
# notes to a flat bullet list. verbatim also preserves the two-space nested
# indentation cliff.toml produces, which is why its `trim = false` is
# mandatory for the same reason. Change either and the release notes silently
# lose structure.

git tag -a "$TAG" --cleanup=verbatim -F /tmp/release-notes.md
git push origin "$TAG"

# Forge-specific: the GitLab-hosted install ships gitlab-release.sh BESIDE this
# script. A GitHub-hosted install has no forge-release script here — its CI
# workflow (assets/github-release.yml) creates the Release object itself with
# `gh release create`, after this script returns.
#
# Resolved relative to THIS FILE rather than the process working directory, so
# one byte-identical script serves both layouts: a consumer repository, where
# ai-release installs the pair into scripts/, and the repository that ships the
# template, where the pair sits under internal/scripts/ because its scripts/ is
# a published path. The working directory is still the repository root either
# way — git-cliff resolves cliff.toml from it — so this is the one lookup that
# must not use it.
if [ -f "$self_dir/gitlab-release.sh" ]; then
  bash "$self_dir/gitlab-release.sh" "$TAG" /tmp/release-notes.md
fi

echo ""
echo "Released $TAG internally. Nothing was published publicly."
echo "No public publish path is configured for this repository. Publishing a"
echo "tag publicly is a separate, deliberate act and nothing here performs it."
