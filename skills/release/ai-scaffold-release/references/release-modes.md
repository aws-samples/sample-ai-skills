# Release modes — the routing table

This skill installs one of two sets of machinery, or both. Which one is decided
**here**, from the table, before the probe in step 1 runs and before any file is
written. The decision is data rather than branching prose in the body so a
reviewer can read all of it on one screen, and so a builder can stop a mis-route
before it costs anything.

## What "present" means

A repository holding any of `scripts/release.sh`, `scripts/gitlab-release.sh`,
`scripts/github-release.sh` or `scripts/promote.sh` is not read against this
table at all. Those are an installation made before the scripts became Python,
and step 1 of the skill refuses it — naming each file, writing nothing — before
this table is consulted.

| Set | Present when the repository root holds |
|---|---|
| **internal** | `cliff.toml` **and** `scripts/release_cli.py` |
| **promote** | `.promote-target` **and** `scripts/promote_cli.py` |

Partially present is not present. Report which files are missing and install the
rest of that set; never overwrite a file that already carries equivalent
machinery.

## The table

Read the request against the left column, then the two state columns.

| The request is about | internal present | promote present | Install | Say, before the probe |
|---|---|---|---|---|
| releases, versioning, a changelog, release notes — and **not** publishing | no | — | **internal only** | "Installing the internal release path. The promote path is not being installed." |
| releases, versioning, a changelog — and **not** publishing | yes | — | **nothing** | "The internal release path is already present. Reporting it and writing nothing." |
| publishing, open-sourcing, promoting, a public copy | yes | no | **promote only** | "The internal release path is already present. Installing the promote path only." |
| publishing, open-sourcing, promoting, a public copy | no | no | **both, internal first** | "No release machinery is present. Installing the internal path first, then the promote path — a promotion consumes a tag the internal path produces." |
| either, or both | yes | yes | **nothing** | "Both halves are already present. Reporting what is present and writing nothing." |

The four install outcomes are *internal only*, *promote only*, *both with
internal first*, and *nothing*. There is no fifth.

**Promote alone, into a repository with no internal path, is not an outcome.**
The promote path promotes an existing annotated tag; a repository with no way to
cut one has nothing to promote, so row 4 installs both rather than leaving a
promote job pointed at an empty tag list. A repository that genuinely cuts tags
by hand and wants only the promote half says so explicitly — that is a request
for the promote path in a repository whose internal path is deliberately absent,
and it is the one case to confirm with the builder rather than resolve from this
table.

## Two properties the table does not express as rows

**The promote path is never a side effect.** No phrasing of a request for the
internal release path installs the promote path. Not "set up releases and I'll
open-source it later", not "releases, and we may publish this", not a repository
that already has a public remote configured. Publishing has to be what is being
asked for, now.

**An ambiguous request resolves to the internal path.** Where the reading is
uncertain, install the internal path only, then report — in the same output —
that the promote path was **not** installed and name the phrasing that installs
it: *"set up a public publish path"*, *"promote releases to a public
repository"*. Guessing wrong toward internal costs a second run; guessing wrong
toward promote writes a `.promote-target` into a repository that never intended
to publish, and an empty configuration file sitting in a repository is worse
than an absent one — somebody eventually fills it in without the conversation
that chooses an allowlist.

## Installing is not promoting

Installing the promote path cuts no tag, pushes no ref, and promotes nothing.
The install ends by reporting the literal command an operator or a CI job runs
to promote, naming the confirmation variable exactly. Every mutation lives in
`assets/promote_cli.py`; the body never performs the push itself.
