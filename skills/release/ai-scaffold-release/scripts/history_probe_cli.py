#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = []
# ///
"""Report two numbers per candidate withheld path: the earliest commit at which
it is still readable in the given ref's reachable history, and the largest size
it ever reached across that range.

A single figure understates exposure: the earliest instance of a file is
systematically its smallest. This tool never modifies history — it only
reports — and it lives in this skill's own scripts/, never copied into a target
repository, because it runs as a standalone audit against a repository it is
invoked from.

Usage:
  uv run scripts/history_probe_cli.py <target-ref> <path> [<path>...]

Exit status is always 0 on a successful probe (findings are informational, not
a refusal) and non-zero only on a usage or git error.
"""

import re
import subprocess  # nosec B404 # runs git and fixed commands, never a shell
import sys

USAGE = "usage: history_probe_cli.py <target-ref> <path> [<path>...]"


def git(*args: str, quiet: bool = False) -> subprocess.CompletedProcess:
    """`git <args>` with its output captured and its status left to the caller.

    `quiet` discards git's own stderr, where the bash redirected it to /dev/null;
    everywhere else it reaches the terminal, as it did.
    """
    return subprocess.run(  # nosec B603 B607 # argument list; git found on PATH
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL if quiet else None,
        encoding="utf-8",
        check=False,
    )


def size_at(commit: str, path: str) -> int:
    """Size a path at one commit.

    A DIRECTORY must be summed recursively over its blobs: `git cat-file -s` on a
    tree returns the size of the tree OBJECT — a list of entry names — not of the
    content under it. Measured: `internal` at v0.2.0 reported 61 bytes against
    687,540 bytes of actual content across 47 files, a four-order-of-magnitude
    understatement of the one path an operator most needs to judge. Understating
    exposure is the single worst thing this tool can do, since the allowlist an
    operator settles on is only as good as the report it was chosen against.
    """
    probe = git("rev-parse", "--verify", "--quiet", f"{commit}:{path}", quiet=True)
    obj = probe.stdout.strip() if probe.returncode == 0 else ""
    if not obj:
        return 0
    kind = git("cat-file", "-t", obj, quiet=True)
    if (kind.stdout.strip() if kind.returncode == 0 else "unknown") == "tree":
        # `-l` puts the blob size in the fourth field; submodule and symlink
        # entries carry a `-` there, so discard any non-numeric field rather than
        # summing it.
        total = 0
        for record in git("ls-tree", "-r", "-l", "-z", obj, quiet=True).stdout.split("\0"):
            fields = record.split("\t", 1)[0].split()
            if len(fields) == 4 and re.fullmatch(r"[0-9]+", fields[3]):
                total += int(fields[3])
        return total
    size = git("cat-file", "-s", obj, quiet=True)
    return int(size.stdout.strip()) if size.returncode == 0 else 0


def probe_path(target_ref: str, path: str) -> None:
    commits = [c for c in git("rev-list", target_ref, "--", path).stdout.splitlines() if c]
    earliest = commits[-1] if commits else ""

    if not earliest:
        print(f"path: {path}")
        print(f"  earliest exposed commit: none — never reachable from {target_ref}")
        print("  maximum size reached:    n/a")
        return

    max_size = 0
    max_commit = ""
    for commit in commits:
        size = size_at(commit, path)
        if size > max_size:
            max_size = size
            max_commit = commit
    largest = max_commit or earliest

    # Count files only for a tree. `git ls-tree -r` against a blob exits 128, which
    # the bash version had to guard against under `set -euo pipefail` because the
    # failure would have silently truncated the report after the first file path —
    # the failure mode this tool exists to avoid.
    file_count = 1
    kind = git("cat-file", "-t", f"{largest}:{path}", quiet=True)
    if (kind.stdout.strip() if kind.returncode == 0 else "blob") == "tree":
        listing = git("ls-tree", "-r", "--name-only", f"{largest}:{path}")
        if listing.returncode != 0:
            sys.exit(listing.returncode)
        file_count = listing.stdout.count("\n")

    print(f"path: {path}")
    print(f"  earliest exposed commit: {earliest}")
    print(f"  maximum size reached:    {max_size} bytes across {file_count} file(s)")
    print(f"  largest at commit:       {largest}")


def main(argv: list) -> int:
    if argv in (["--help"], ["-h"]):
        print(USAGE)
        print()
        print(__doc__.split("\n\n", 1)[0].replace("\n", " "))
        return 0
    if len(argv) < 2:
        print(USAGE, file=sys.stderr)
        return 2

    target_ref, *paths = argv
    if git("rev-parse", "--verify", "--quiet", target_ref).returncode != 0:
        print(f"error: {target_ref} does not resolve in this repository", file=sys.stderr)
        return 2

    for path in paths:
        probe_path(target_ref, path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
