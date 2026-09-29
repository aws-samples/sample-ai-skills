#!/usr/bin/env bash
# Report two numbers per candidate withheld path: the earliest commit at which
# it is still readable in the given ref's reachable history, and the largest
# size it ever reached across that range.
#
# A single figure understates exposure: the earliest instance of a file is
# systematically its smallest. This tool never modifies history — it only
# reports — and it lives in this skill's own scripts/, never copied into a
# target repository, because it runs as a standalone audit against a
# repository it is invoked from.
#
# Usage:
#   scripts/history-probe.sh <target-ref> <path> [<path>...]
#
# Exit status is always 0 on a successful probe (findings are informational,
# not a refusal) and non-zero only on a usage or git error.

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "usage: history-probe.sh <target-ref> <path> [<path>...]" >&2
  exit 2
fi

TARGET_REF="$1"
shift

if ! git rev-parse --verify --quiet "$TARGET_REF" >/dev/null; then
  echo "error: $TARGET_REF does not resolve in this repository" >&2
  exit 2
fi

probe_path() {
  local path="$1"
  local earliest max_size max_commit size commit file_count

  earliest="$(git rev-list "$TARGET_REF" -- "$path" | tail -1 || true)"

  if [ -z "$earliest" ]; then
    echo "path: $path"
    echo "  earliest exposed commit: none — never reachable from $TARGET_REF"
    echo "  maximum size reached:    n/a"
    return 0
  fi

  # Size a path at one commit. A DIRECTORY must be summed recursively over its
  # blobs: `git cat-file -s` on a tree returns the size of the tree OBJECT — a
  # list of entry names — not of the content under it. Measured: `internal` at
  # v0.2.0 reported 61 bytes against 687,540 bytes of actual content across 47
  # files, a four-order-of-magnitude understatement of the one path an operator
  # most needs to judge. Understating exposure is the single worst thing this
  # tool can do, since the allowlist an operator settles on is only as good as
  # the report it was chosen against.
  size_at() {
    local commit="$1" path="$2" object kind
    object="$(git rev-parse --verify --quiet "${commit}:${path}" 2>/dev/null || true)"
    [ -z "$object" ] && { echo 0; return 0; }
    kind="$(git cat-file -t "$object" 2>/dev/null || echo unknown)"
    if [ "$kind" = "tree" ]; then
      # `-l` puts the blob size in field 4; submodule and symlink entries carry
      # a `-` there, so discard any non-numeric field rather than summing it.
      git ls-tree -r -l "$object" 2>/dev/null |
        awk '$4 ~ /^[0-9]+$/ { s += $4 } END { print s + 0 }'
    else
      git cat-file -s "$object" 2>/dev/null || echo 0
    fi
  }

  max_size=0
  max_commit=""
  while IFS= read -r commit; do
    [ -z "$commit" ] && continue
    size="$(size_at "$commit" "$path")"
    [ -z "$size" ] && size=0
    if [ "$size" -gt "$max_size" ]; then
      max_size="$size"
      max_commit="$commit"
    fi
  done < <(git rev-list "$TARGET_REF" -- "$path")

  # Count files only for a tree. `git ls-tree -r` against a blob exits 128, and
  # under `set -euo pipefail` that failure inside a command substitution aborts
  # the whole probe — silently truncating the report after the first file path,
  # which is the failure mode this tool exists to avoid.
  file_count=1
  if [ "$(git cat-file -t "${max_commit:-$earliest}:${path}" 2>/dev/null || echo blob)" = "tree" ]; then
    file_count="$(git ls-tree -r --name-only "${max_commit:-$earliest}:${path}" | wc -l | tr -d ' ')"
  fi

  echo "path: $path"
  echo "  earliest exposed commit: $earliest"
  echo "  maximum size reached:    ${max_size} bytes across ${file_count} file(s)"
  echo "  largest at commit:       ${max_commit:-$earliest}"
}

for path in "$@"; do
  probe_path "$path"
done
