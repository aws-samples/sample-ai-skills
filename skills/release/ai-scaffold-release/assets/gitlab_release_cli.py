#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = []
# ///
"""Create a GitLab Release object for an existing tag.

Usage: uv run scripts/gitlab_release_cli.py <tag> <notes-file>

Why the API rather than the `release:` CI keyword: that keyword is implemented
by `release-cli`, a Go binary that must be present in the job image, and the
release jobs run on a Python image that does not carry it. The REST API needs no
extra tooling.

A tag alone is not a release. Bare tags with no Release object and no notes are
not a substitute for this step.

Runs from CI (CI_JOB_TOKEN, issued automatically) OR from a workstation
(GITLAB_TOKEN, a personal access token) — a release cut without CI available is
a supported path, not a partial failure. Credentials are checked BEFORE the
notes file is even opened, so a workstation run with neither variable set fails
at the top of this script rather than after release_cli.py has already pushed
the tag to origin.

THE CREDENTIAL TRAVELS ONLY IN A REQUEST HEADER. It is never an argument to a
process, never printed, and never written to a file. Every failure is reported
as a message this script builds, and no traceback is ever printed, because a
traceback can carry a value the script held.
"""

import json
import os
import signal
import sys
import urllib.error
import urllib.request
from pathlib import Path

USAGE = "usage: gitlab_release_cli.py <tag> <notes-file>"


class NoRedirects(urllib.request.HTTPRedirectHandler):
    """Report a redirect as the response it is, as curl without -L did.

    Following one would resend the credential header to wherever the redirect
    points, and a redirect from a forge API is an answer to report — a sign-in
    portal in front of the instance, say — not a location to try next.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def err(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)


def refuse(*lines: str):
    err(*lines)
    sys.exit(1)


def main(argv: list) -> int:
    if argv in (["--help"], ["-h"]):
        print(USAGE)
        print()
        print(__doc__.split("\n\n", 1)[0])
        return 0

    if len(argv) < 2 or not argv[0] or not argv[1]:
        refuse(USAGE)
    tag, notes_file = argv[0], Path(argv[1])

    # -----------------------------------------------------------------------
    # Credential pre-flight — BEFORE anything is created, and before the notes
    # file is read. CI_JOB_TOKEN is preferred (scoped, short-lived, no setup);
    # the PRIVATE-TOKEN header with a personal GITLAB_TOKEN is the workstation
    # fallback release_cli.py advertises. Refusing here, rather than sending a
    # request with no auth header, is what keeps the failure from landing after
    # the tag is already on origin.
    # -----------------------------------------------------------------------
    if os.environ.get("CI_JOB_TOKEN", ""):
        header = ("JOB-TOKEN", os.environ["CI_JOB_TOKEN"])
    elif os.environ.get("GITLAB_TOKEN", ""):
        header = ("PRIVATE-TOKEN", os.environ["GITLAB_TOKEN"])
    else:
        refuse(
            "error: neither CI_JOB_TOKEN nor GITLAB_TOKEN is set",
            "hint: in CI, CI_JOB_TOKEN is issued automatically — this script should",
            "      not be run manually in that environment.",
            "hint: from a workstation, export GITLAB_TOKEN with a personal access",
            "      token carrying api scope, then re-run.",
            f"hint: the tag {tag} was pushed successfully by release_cli.py; only the",
            "      Release object is missing. Re-running this script once",
            "      credentials are set is safe — it is idempotent.",
        )

    # The instance comes from the job, or is refused — never defaulted. Any
    # default would name one organisation's instance, and a workstation run
    # elsewhere would target it silently.
    api = os.environ.get("CI_API_V4_URL", "")
    if not api:
        refuse(
            "error: CI_API_V4_URL is unset — pass it explicitly outside CI, e.g."
            " CI_API_V4_URL=https://<gitlab-host>/api/v4"
        )
    project = os.environ.get("CI_PROJECT_ID", "")
    if not project:
        refuse(
            "error: CI_PROJECT_ID is unset — pass it explicitly outside CI, e.g."
            " CI_PROJECT_ID=<project-id>"
        )

    if not notes_file.is_file():
        refuse(f"error: notes file not found: {notes_file}")

    # The description is the notes byte for byte: read without newline
    # translation, and serialised by json rather than by string interpolation,
    # since the notes carry newlines, backticks, quotes, and asterisks.
    with open(notes_file, encoding="utf-8", newline="") as fh:
        description = fh.read()
    payload = json.dumps({"name": tag, "tag_name": tag, "description": description})

    # The response is held in memory and never written anywhere, so there is no
    # buffer file for another local user to pre-empt and none to leave behind.
    url = f"{api}/projects/{project}/releases"
    request = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        method="POST",
        headers={header[0]: header[1], "Content-Type": "application/json"},
    )
    try:
        with urllib.request.build_opener(NoRedirects).open(request) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    except urllib.error.URLError as error:
        failed(tag, f"error: could not reach {url}: {error.reason}")
    except Exception as error:
        # The type alone: an exception's text can quote a header value.
        failed(tag, f"error: the request to {url} failed ({type(error).__name__})")

    if status == 201:
        print(f"ok: created GitLab Release {tag}")
    elif status == 409:
        # Idempotent: a Release for this tag already exists. Not a failure — the
        # tag is pushed and the Release is present, which is the desired end
        # state.
        print(f"ok: GitLab Release {tag} already exists")
    else:
        err(f"error: failed to create GitLab Release {tag} (HTTP {status})")
        sys.stderr.flush()
        sys.stderr.buffer.write(body)
        sys.stderr.buffer.flush()
        failed(tag, "")
    return 0


def failed(tag: str, message: str):
    err(
        message,
        "hint: the tag was pushed successfully — only the Release object",
        "      failed. Re-running this script is safe; it is idempotent.",
    )
    sys.exit(1)


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="surrogateescape", line_buffering=True)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    sys.exit(main(sys.argv[1:]))
