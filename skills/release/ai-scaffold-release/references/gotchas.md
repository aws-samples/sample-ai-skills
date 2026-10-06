# Gotchas

Defects measured in the reference implementations this skill's templates are
transcribed from, corrected here rather than reproduced. Read this before
touching any of the five bundled templates — each entry exists because getting
it wrong was reachable, not hypothetical.

## `git describe --tags --abbrev=0` needs `--match`

Without `--match='v[0-9]*.[0-9]*.[0-9]*'`, the latest-tag read sees every tag
in the repository while the derived version is filtered by `tag_pattern`. One
stray non-release tag (a CI marker, an experiment tag, anything not shaped like
`vX.Y.Z`) then makes the major-bump comparison error with "integer expression
expected" — and `set -e` is no protection, because a failure inside an `if`
condition is exempt by design. The comparison silently short-circuits and a
major bump can proceed unconfirmed.

## The annotation cleanup mode is load-bearing, not stylistic

`git tag -a ... -F <file>` defaults to `--cleanup=strip`, which removes every
line starting with `#` — every Markdown heading the release notes contain —
and exits 0 while doing it. `--cleanup=verbatim` is mandatory. This is the same
reason `cliff.toml`'s `trim = false` is mandatory: change either and the
published notes silently lose structure, and nothing in the exit code says so.

## A refusal that fires after the tag exists is not a gate

The GitLab release script's original form hard-refused outside CI, while
the release script advertised a workstation path — so a workstation release pushes
the tag and only THEN fails on the Release-object step, completing the least
reversible action (the push) and losing the recoverable one (creating the
object, which is idempotent and safe to retry). Every credential check in
these scripts runs before the tag is created, never after.

## A tagless repository cannot bootstrap itself

`git-cliff --bumped-version` on a repository with no tags exits 1 with "Next
version (0.1.0) does not match the tag pattern" — a message that names the
symptom (a version shape mismatch) rather than the cause (nothing to derive
from). `scripts/release_cli.py` intercepts this state before calling `git-cliff` at
all and prints the actual bootstrap command instead of surfacing that error.

## A confirmation implemented as a question fails open

On a harness with no question mechanism, the branch that would have stopped
the write is the branch that cannot execute. Every gate here — `CONFIRM_VERSION`
and, in the mirror skill, `CONFIRM_TAG`/`ACK_*` — is a variable equality check
evaluated identically whether or not a question mechanism exists, never a
question that degrades to "proceed" when nothing can ask it.

## "Derived equals current tag" has two causes

Only one of them is "nothing to release." The other is a previous run that tagged
locally and failed before pushing — `git describe` reports the local tag,
derivation reports it back, and a naive check would say "nothing to do" and
exit 0 while a release sits unpublished. `scripts/release_cli.py` confirms the
local tag is present on origin via `git ls-remote` before believing the no-op.

## A heading is not evidence of content

`--tag` always stamps the version heading, so notes with a heading and zero
entries pass a heading-only check. This is reachable: any commit matching no
parser at all (a bare `wip`, a plain `Add thing`, a merge commit) still derives
a patch bump but groups into no section. `scripts/release_cli.py` asserts both a
heading (`^## \[`) and at least one entry (`^- `) before tagging.
