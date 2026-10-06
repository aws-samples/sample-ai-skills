#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = ["git-cliff==2.10.1"]
# ///
"""Cut an internal release: tag origin and create a GitLab Release.

Usage: uv run scripts/release_cli.py

  Takes NO arguments. The version is DERIVED from tags and Conventional Commit
  history — there is no VERSION file and no way to request a version. That is
  deliberate: a requestable version is a version somebody gets wrong.

Environment:
  PREVIEW=1         print what would be released and exit 0. Creates nothing,
                    and needs no network.
  CONFIRM_VERSION   required, equal to the derived tag, when the release
                    raises the MAJOR version.

Runs identically in CI (the gitlab:release job) and from a workstation, which
is what makes a release possible when CI is unavailable.

Cutting an internal release publishes NOTHING publicly. Publishing to a public
remote is a separate, deliberate act — see the release how-to.

---------------------------------------------------------------------------
THE ORDERING IS THE DESIGN. Do not reorder these steps.
---------------------------------------------------------------------------

  0. Tagless refusal.       Before derivation, because derivation is what fails.
  1. Derive.                Everything below is a statement about this value.
  2. Preview, exit 0.       First, because everything below touches the network.
  3. No-op, exit 0.         "Nothing to release" is an answer, not a failure —
                            but only once origin confirms the tag was pushed.
  4. Major guard.           Refuse before spending work on notes.
  5. Tag hygiene.           A disagreeing tag means derivation read the wrong base.
  6. Tag absence.           The double-tag guard.
  7. Notes + heading assert.
  8. Tag, push, Release object.

Steps 4-7 all run BEFORE the tag exists, because a gate that fires after
tagging is not a gate — the tag would already be on origin by the time it
complained.
"""

import os
import re
import signal
import subprocess  # nosec B404 # runs git and fixed commands, never a shell
import sys
import tempfile
from pathlib import Path

# This script's own directory. Every hint below and the forge probe near the end
# are built from it rather than from a hardcoded `scripts/`, because the pair is
# installed into `scripts/` in a consumer repository and lives under
# `internal/scripts/` in the repository that ships this template. One
# byte-identical file has to be right in both, and a hint naming a path that does
# not exist sends a maintainer looking for a missing file.
SELF_DIR = Path(__file__).resolve().parent

# git-cliff comes from this script's own environment — the one `uv run` builds
# from the dependency declared above — and never from PATH, so a different
# git-cliff installed elsewhere cannot be the one that derives the version. Not
# resolved: the environment's interpreter is a link to a base installation, and
# it is the link's directory that holds the environment's executables.
GIT_CLIFF = Path(sys.executable).parent / ("git-cliff.exe" if os.name == "nt" else "git-cliff")

# The forge-release script this one runs after pushing the tag, when it is
# installed beside this file. See step 8.
GITLAB_RELEASE = SELF_DIR / "gitlab_release_cli.py"


def err(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)


def refuse(*lines: str):
    err(*lines)
    sys.exit(1)


def capture(*argv, quiet: bool = False) -> subprocess.CompletedProcess:
    """Run a command with its stdout captured and its status left to the caller.

    `quiet` discards its stderr where the bash version redirected it to
    /dev/null; everywhere else it reaches the terminal. A list, never a shell.
    """
    try:
        return subprocess.run(  # nosec B603 # argument list of fixed commands, never a shell
            [str(a) for a in argv],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL if quiet else None,
            encoding="utf-8",
            errors="surrogateescape",
            check=False,
        )
    except FileNotFoundError:
        refuse(f"error: {argv[0]} is not installed")


def output(*argv) -> str:
    """A command substitution under `set -e`: stdout without its trailing
    newlines, or this script exits with the command's own status."""
    result = capture(*argv)
    if result.returncode != 0:
        sys.exit(result.returncode)
    return result.stdout.rstrip("\n")


def call(*argv, **kwargs) -> None:
    """A bare command under `set -e`: its output passes straight through, and a
    failure ends this script with the command's own status."""
    try:
        status = subprocess.run([str(a) for a in argv], check=False, **kwargs).returncode  # nosec B603 # argument list, never a shell
    except FileNotFoundError:
        refuse(f"error: {argv[0]} is not installed")
    if status != 0:
        sys.exit(status)


def on_origin(tag: str) -> bool:
    """Whether origin lists `tag`."""
    return tag in capture("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}").stdout


def is_integer(text: str) -> bool:
    return re.fullmatch(r"[0-9]+", text) is not None


def check_tag_hygiene() -> None:
    """Every local release tag must point at the same object as origin's tag of
    the same name. A disagreeing tag poisons both computations the release path
    depends on: version derivation reads the wrong base (`git describe` returns
    the previous tag) and any publish range resolves against the wrong commit.

    Near-tautological in CI, which fetches --tags --force into a fresh clone. It
    earns its lines locally, where the failure is silent.
    """
    disagreements = 0
    for line in capture("git", "ls-remote", "--tags", "origin").stdout.splitlines():
        # The anchored pattern also drops the peeled entries
        # (refs/tags/<name>^{}), which restate the annotated tag's target;
        # comparing the tag object itself is what matters here.
        if not re.search(r"refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$", line):
            continue
        origin_sha, _, ref = line.partition("\t")
        tag = ref.removeprefix("refs/tags/")

        # A tag that exists on origin but not locally is not a disagreement —
        # there is nothing local to be wrong. Only a name present on BOTH sides
        # can disagree.
        local = capture("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")
        if local.returncode != 0:
            continue
        local_sha = local.stdout.rstrip("\n")

        if local_sha != origin_sha:
            err(
                f"error: local tag {tag} disagrees with origin",
                f"  local:  {local_sha}",
                f"  origin: {origin_sha}",
            )
            disagreements += 1

    if disagreements > 0:
        refuse(
            "hint: repair this clone with: git fetch origin --tags --force",
            "hint: nothing was created.",
        )

    print("ok: local release tags agree with origin")


def main(argv: list) -> int:
    if argv in (["--help"], ["-h"]):
        print("usage: release_cli.py")
        print(__doc__.split("\n---", 1)[0].split("\n", 1)[1])
        return 0

    if argv:
        refuse(
            f"error: release_cli.py takes no arguments (got: {' '.join(argv)})",
            "hint: the version is derived from commit history, not supplied. To",
            f"      preview, run: PREVIEW=1 uv run {sys.argv[0]}",
        )

    # -----------------------------------------------------------------------
    # 0. Tagless refusal
    # -----------------------------------------------------------------------
    #
    # Derivation cannot bootstrap itself: on a repository with no tags,
    # `git-cliff --bumped-version` exits 1 with "Next version (0.1.0) does not
    # match the tag pattern", because its no-release fallback emits a bare
    # `0.1.0` while `tag_pattern` requires a leading `v`. Failing to derive means
    # no tag is created, so there is still nothing to derive from next time.
    #
    # That raw error names nothing about the cause, so refuse in terms of the
    # actual state and print the one-time action. The bootstrap version is NOT
    # inferred: where the tag sits decides which commits the first derived
    # release describes, so it is a choice an operator makes rather than one a
    # script makes for them.
    if not capture("git", "tag", "--list").stdout.rstrip("\n"):
        root = output("git", "rev-list", "--max-parents=0", "HEAD")
        refuse(
            "error: this repository has no tags, so no version can be derived",
            "hint: version derivation walks back to the newest release tag. With",
            "      none, there is no base to derive from, and creating one is a",
            "      one-time bootstrap an operator performs deliberately:",
            f"        git tag -a v0.1.0 --cleanup=verbatim -F <annotation-file> {root}",
            "        git push origin v0.1.0",
            "hint: the commit you tag decides which commits the FIRST derived",
            "      release describes — tagging the root commit puts all of history",
            "      inside it. --cleanup=verbatim is mandatory: the default cleanup",
            "      mode strips every '#'-leading line — every Markdown heading —",
            "      and exits 0 doing it. See the release how-to. Nothing",
            "      was created.",
        )

    # -----------------------------------------------------------------------
    # 1. Derive
    # -----------------------------------------------------------------------
    if not GIT_CLIFF.is_file():
        refuse(
            f"error: git-cliff is not installed in this script's environment ({GIT_CLIFF.parent})",
            f"hint: run it with uv, which installs the version it declares: uv run {sys.argv[0]}",
        )
    tag = output(GIT_CLIFF, "--bumped-version")
    described = capture(
        "git", "describe", "--tags", "--abbrev=0", "--match=v[0-9]*.[0-9]*.[0-9]*", quiet=True
    )
    latest = described.stdout.rstrip("\n") if described.returncode == 0 else "none"

    # -----------------------------------------------------------------------
    # 2. Preview
    # -----------------------------------------------------------------------
    #
    # One script, one early return, rather than a separate preview path — so the
    # preview cannot report notes that differ from what a release publishes.
    #
    # FIRST, before every other check, because none of the others are
    # network-free: even the no-op below asks origin whether the newest tag was
    # pushed. A preview that requires the network is a preview that fails on a
    # plane. The cost is that a preview does not detect a poisoned clone —
    # acceptable, because it creates nothing and the release path still refuses.
    if os.environ.get("PREVIEW", "") == "1":
        print(f"current release: {latest}")
        print(f"would release:   {tag}")

        if tag == latest:
            print("")
            print(f"Nothing to release — no commits since {latest} affect the version.")
            print("Only conventional commits (feat:, fix:, ...) derive a new version.")
            return 0

        print("")
        print(f"--- release notes for {tag} ---")
        call(GIT_CLIFF, "--unreleased", "--tag", tag, "--strip", "all")
        print("--- end release notes ---")
        print("")
        print("Nothing was created. To cut this release, run the 'gitlab:release' job.")
        return 0

    # -----------------------------------------------------------------------
    # 3. The idempotent no-op
    # -----------------------------------------------------------------------
    #
    # Exits 0 DELIBERATELY. The release job is a button that can be clicked
    # speculatively, and a red pipeline for "you clicked it and there was nothing
    # to do" is a red pipeline everyone learns to ignore — at which point it also
    # hides the one time it means something.
    #
    # But "derived equals newest" has TWO causes, and only one of them is nothing
    # to do. If a previous run created the tag locally and then failed to push
    # it, `git describe` reports it, derivation reports it back, and this branch
    # would say "nothing to release" and exit 0 — leaving a release that never
    # reached origin and reporting success for it. So the local tag is confirmed
    # present on origin before the no-op is believed. This costs one
    # `git ls-remote`, which is why the preview above returns before reaching it.
    if tag == latest:
        if on_origin(latest):
            print(f"Nothing to release — derived version equals the current tag ({latest}).")
            print("Only conventional commits (feat:, fix:, ...) derive a new version.")
            print("Nothing was created.")
            return 0

        refuse(
            f"error: tag {latest} exists locally but NOT on origin",
            "hint: a previous release run created the tag and failed before",
            "      pushing it, so this release was never published.",
            "hint: push it and create the Release object:",
            f"        git push origin {latest}",
            f"        uv run {GITLAB_RELEASE} {latest} <notes-file>",
            f"hint: or discard it and start over: git tag -d {latest}",
        )

    # -----------------------------------------------------------------------
    # 4. Major-version guard
    # -----------------------------------------------------------------------
    #
    # Keyed on the SHAPE of the derived version, not on commit text, so it holds
    # before and after 1.0. cliff.toml's `breaking_always_bump_major = false` is
    # retained as belt and braces but is INERT once the major reaches 1 —
    # verified: at v1.0.0 a `feat!:` still derives v2.0.0. This guard is what
    # survives.
    #
    # CONFIRM_VERSION must equal the derived tag exactly rather than being a
    # boolean, so a stale confirmation fails closed: if history moves between
    # the refusal and the retry, the derived version changes and the old value
    # no longer matches.
    #
    # LATEST is read with --match above, so a stray non-release tag cannot
    # become the comparison base. A major component that is still not an integer
    # compares as not greater, which is what the bash version's `[ -gt ]` did
    # when it failed inside the `if`.
    if latest != "none":
        new_major = tag.removeprefix("v").split(".", 1)[0]
        old_major = latest.removeprefix("v").split(".", 1)[0]

        if (
            is_integer(new_major)
            and is_integer(old_major)
            and int(new_major) > int(old_major)
            and os.environ.get("CONFIRM_VERSION", "") != tag
        ):
            refuse(
                f"error: this release changes the MAJOR version ({latest} -> {tag})",
                f"hint: re-run with CONFIRM_VERSION={tag}",
                "hint: nothing was created. Read the notes with PREVIEW=1 first if",
                "      you did not expect a major bump.",
            )

    # -----------------------------------------------------------------------
    # 5. Tag hygiene
    # -----------------------------------------------------------------------
    check_tag_hygiene()

    # -----------------------------------------------------------------------
    # 6. Tag absence — the double-tag guard
    # -----------------------------------------------------------------------
    #
    # Checked on BOTH sides. A local-only tag would make `git tag -a` fail with
    # a less informative message; an origin-side tag means the version is
    # already released and this run must not proceed.
    if capture("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").returncode == 0:
        refuse(
            f"error: tag {tag} already exists locally",
            f"hint: if it was created by a failed run, delete it (git tag -d {tag})",
            f"      and re-run. If it exists on origin too, {tag} is already released.",
        )

    if on_origin(tag):
        refuse(
            f"error: tag {tag} already exists on origin — nothing to release",
            f"hint: {tag} has already been released. If the GitLab Release object is",
            "      missing but the tag exists, run gitlab_release_cli.py directly:",
            f"        uv run {GITLAB_RELEASE} {tag} <notes-file>",
        )

    print(f"Releasing {tag} (current: {latest})")

    # -----------------------------------------------------------------------
    # 7. Notes
    # -----------------------------------------------------------------------
    #
    # --tag stamps the heading as "## [X.Y.Z] - <date>". Without it the notes
    # are headed "## [Unreleased]", which is wrong on a tag that names a version
    # — and any publish path that reads this annotation requires a '## ['
    # heading in it.
    #
    # Generated HERE, from current history. There is no committed changelog to
    # read from, and generating fresh is what makes the published notes complete.
    #
    # Into a file mkstemp creates, never a fixed path. A predictable name on a
    # shared host can be created first by another user, as a file or a symlink,
    # and whatever it holds becomes the tag annotation and the Release
    # description — text this repository publishes. mkstemp creates it 0600 and
    # unguessable, and the `finally` removes it on every exit, including a
    # refusal below and a failed push. Allocated only now, after the preview and
    # the no-op have returned, so neither creates a file. The descriptor is
    # closed before git reopens the file by name, which Windows requires.
    fd, notes_name = tempfile.mkstemp(prefix="release-notes.", suffix=".md")
    notes = Path(notes_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            call(GIT_CLIFF, "--unreleased", "--tag", tag, "--strip", "all", stdout=fh)
        publish(tag, notes)
    finally:
        notes.unlink(missing_ok=True)
    return 0


def publish(tag: str, notes: Path) -> None:
    """Steps 7 to 8, against the notes file step 7 generated."""
    text = notes.read_bytes().decode("utf-8", "surrogateescape")

    # TWO assertions, because the heading alone is not evidence of content.
    #
    # The heading check protects the contract a consumer reads: the notes become
    # both the tag annotation and the GitLab Release description, and a release
    # that names a version without a version heading is a release nobody can
    # navigate.
    if not re.search(r"(?m)^## \[", text):
        refuse(
            f"error: generated notes for {tag} contain no version heading",
            "hint: a '## [' heading is required in the tag annotation, which",
            "      becomes the GitLab Release description verbatim. Refusing to",
            "      create a tag whose notes have no version heading. Nothing was",
            "      created.",
        )

    # The content check catches a CONTENTLESS release, which the heading check
    # cannot see: `--tag` always stamps the heading, so notes with a heading and
    # no entries pass it. That state is reachable, and not exotic —
    #
    #   a commit matching NO parser at all (a bare "wip", a plain "Add thing", or
    #   a "Merge branch ..." commit) derives a PATCH but is grouped into nothing,
    #   so it contributes a version bump and zero entries. Verified: a chore-only
    #   branch merged with --no-ff derives a patch whose notes are one heading
    #   and nothing else.
    #
    # Only parsers with `skip = true` (^chore, ^style, ^test) suppress the bump;
    # everything unmatched still bumps. So refuse rather than publish a release
    # that describes nothing.
    if not re.search(r"(?m)^- ", text):
        err(f"error: generated notes for {tag} contain a heading but no entries", "")
        sys.stderr.flush()
        sys.stderr.buffer.write(notes.read_bytes())
        sys.stderr.buffer.flush()
        refuse(
            "",
            "hint: every commit in this window is either skipped (chore:, style:,",
            "      test:) or matches no conventional type at all. An unmatched",
            "      commit — a bare 'wip', a plain 'Add thing', or a merge commit —",
            "      still derives a patch bump but is grouped into nothing, which is",
            "      how a version can be derivable with nothing to say.",
            "hint: reword the commits conventionally, or leave the release uncut.",
            "      Nothing was created.",
        )

    # -----------------------------------------------------------------------
    # 7b. Credential pre-flight — BEFORE the tag exists
    # -----------------------------------------------------------------------
    #
    # Checked here, not left for gitlab_release_cli.py to discover after step 8
    # has already pushed the tag. A release object can be recreated any time; a
    # pushed tag cannot be un-pushed without a force-delete on origin. So the
    # forge-release credential is verified while nothing irreversible has
    # happened yet, and the workstation path (GITLAB_TOKEN, a personal access
    # token) is accepted as an alternative to CI_JOB_TOKEN rather than treated as
    # a partial failure.
    if not any(os.environ.get(name, "") for name in ("CI_JOB_TOKEN", "GITLAB_TOKEN", "GITHUB_TOKEN")):
        refuse(
            "error: no forge credential is set (checked CI_JOB_TOKEN, GITLAB_TOKEN,",
            "      GITHUB_TOKEN)",
            "hint: creating the forge Release object needs one of them. In CI,",
            "      CI_JOB_TOKEN (GitLab) is issued automatically. From a",
            "      workstation, export GITLAB_TOKEN with a personal access token",
            "      carrying api scope, then re-run.",
            "hint: refusing before the tag is created — nothing was created.",
        )

    # -----------------------------------------------------------------------
    # 8. Tag, push, publish internally
    # -----------------------------------------------------------------------
    #
    # `--cleanup=verbatim -F` is LOAD-BEARING, not stylistic. Git's default
    # cleanup mode strips #-leading lines as comments and reflows content — and
    # EXITS 0 while doing it, so the loss is silent. The notes are Markdown whose
    # every section heading starts with `#`, so the default would reduce grouped
    # notes to a flat bullet list. verbatim also preserves the two-space nested
    # indentation cliff.toml produces, which is why its `trim = false` is
    # mandatory for the same reason. Change either and the release notes
    # silently lose structure.
    call("git", "tag", "-a", tag, "--cleanup=verbatim", "-F", notes)
    call("git", "push", "origin", tag)

    # Forge-specific: the GitLab-hosted install ships gitlab_release_cli.py
    # BESIDE this script. A GitHub-hosted install has no forge-release script
    # here — its CI workflow (assets/github-release.yml) creates the Release
    # object itself with `gh release create --notes-from-tag`, after this script
    # returns.
    #
    # Resolved relative to THIS FILE rather than the process working directory,
    # so one byte-identical script serves both layouts: a consumer repository,
    # where ai-scaffold-release installs the pair into scripts/, and the
    # repository that ships the template, where the pair sits under
    # internal/scripts/ because its scripts/ is a published path. The working
    # directory is still the repository root either way — git-cliff resolves
    # cliff.toml from it — so this is the one lookup that must not use it.
    #
    # Run with this script's own interpreter: the forge script needs nothing
    # beyond the standard library, so a second `uv run` would build a second
    # environment for no gain.
    if GITLAB_RELEASE.is_file():
        call(sys.executable, GITLAB_RELEASE, tag, notes)

    print("")
    print(f"Released {tag} internally. Nothing was published publicly.")
    print("No public publish path is configured for this repository. Publishing a")
    print("tag publicly is a separate, deliberate act and nothing here performs it.")


if __name__ == "__main__":
    # Line-buffered, so a line printed here cannot land after the output of a
    # command run next, and UTF-8 with surrogateescape, so commit subjects pass
    # through as the bytes git gave.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="surrogateescape", line_buffering=True)
    # A terminated run still leaves through `finally`, which removes the notes.
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    sys.exit(main(sys.argv[1:]))
