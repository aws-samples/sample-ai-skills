#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = []
# ///
"""Create the GitHub Release for a tag a promotion has pushed.

  uv run <this-script> [TAG]                             # dry run — reports, creates nothing
  CONFIRM_SHA=<tag object id> uv run <this-script> TAG   # creates the Release

A tag pushed to GitHub gets no Release object, so without this step the target's
Releases page stays empty while the internal forge shows a Release for the same
tag. Run after promote_cli.py, in the same job, with the same tag. It is a
separate script so that promote_cli.py carries no condition on the target's
forge.

THE BODY IS THE TAG'S ANNOTATION, BYTE FOR BYTE — the one promote_cli.py reuses.
An annotation ends in a blank line, and a body one newline short is a different
body to the comparison below, so nothing here strips or normalises it.

SAFE TO RE-RUN, and it never edits a published Release. No Release: it creates
one. A Release with an identical body: success, no write. A Release with a
different body: it refuses and prints the difference, because someone changed it
on purpose or the annotation is not the one that was published.

THE TAG MUST ALREADY BE ON THE TARGET. GitHub answers a Release for a missing tag
by creating a lightweight tag at the default branch's tip — a tag nobody
promoted — so the tag is looked up before anything is written.

TAG defaults to the newest strict-semver tag on origin, the rule promote_cli.py
applies, so a job that passes neither script a tag has both resolve the same one.
CONFIRM_SHA is read from the ENVIRONMENT only, and an absent confirmation is the
dry run, which contacts no host. It is the object id of the tag in THIS clone —
the confirmation promote_cli.py takes, so one value authorizes both steps of a job.

The credential is PROMOTE_TOKEN, the push credential, then GITHUB_TOKEN for a
workstation run. It travels only in a request header: never an argument to a
process, never printed, never written to a file. No traceback is ever printed,
because a traceback can carry a value the script held.
"""

import difflib
import json
import os
import re
import signal
import subprocess  # nosec B404 # runs git and fixed commands, never a shell
import sys
import urllib.error
import urllib.request
from pathlib import Path

USAGE = "usage: github_release_cli.py [TAG]"

# The two forms a GitHub remote is written in, on github.com itself. Anything
# else — another forge, a GitHub Enterprise host, a URL carrying a credential —
# is refused, before any host is contacted.
GITHUB_URL = re.compile(r"(https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


class NoRedirects(urllib.request.HTTPRedirectHandler):
    """Report a redirect as the response it is, as curl without -L did, rather
    than resend the credential header to wherever it points."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class State:
    """What the exit path needs: whether the run was confirmed, and the tag."""

    confirmed = False
    tag = ""
    tag_id = ""


def err(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)


def die(message: str, *hints: str):
    err(f"error: {message}", *(f"hint: {hint}" for hint in hints))
    sys.exit(1)


def git(*args: str, quiet: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 B607 # argument list; git found on PATH
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL if quiet else None,
        check=False,
    )


def newest_semver_tag() -> str:
    """The newest strict-semver tag on origin, by version rather than by string —
    a string sort ranks v0.1.2 above v0.1.10."""
    listing = git("ls-remote", "--tags", "--refs", "origin", quiet=True).stdout.decode("utf-8", "surrogateescape")
    tags = []
    for line in listing.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            name = fields[1].removeprefix("refs/tags/")
            match = re.fullmatch(r"v([0-9]+)\.([0-9]+)\.([0-9]+)", name)
            if match:
                tags.append((tuple(int(n) for n in match.groups()), name))
    return max(tags)[1] if tags else ""


def field(body: bytes, *keys: str) -> str:
    """A field of a JSON response, by key path. A null or absent field is empty,
    so a Release with no body compares as an empty one."""
    try:
        value = json.loads(body)
    except ValueError:
        die("the GitHub API returned a body that is not JSON")
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return "" if value is None else str(value)


def run(argv: list, state: State) -> int:
    api_base = (os.environ.get("GITHUB_API_URL", "") or "https://api.github.com").removesuffix("/")
    # No chdir: every path below is absolute, so the invocation this script
    # prints stays correct for the caller's own directory, which is where the
    # printed commands are run.
    toplevel = git("rev-parse", "--show-toplevel")
    if toplevel.returncode != 0:
        return toplevel.returncode
    config_file = Path(toplevel.stdout.decode("utf-8", "surrogateescape").rstrip("\n")) / ".promote-target"
    self_path = sys.argv[0]

    # --- the target: parsed, never sourced, and GitHub or refused ----------
    if not config_file.is_file():
        die(f"no promote configuration at {config_file}")
    public_target = ""
    for line in config_file.read_bytes().decode("utf-8", "surrogateescape").split("\n"):
        if line.startswith("PUBLIC_TARGET="):
            public_target = line.partition("=")[2]
    if not public_target:
        die(f"{config_file} declares no PUBLIC_TARGET")
    match = GITHUB_URL.fullmatch(public_target)
    if not match:
        die(
            f"PUBLIC_TARGET is not a GitHub repository: {public_target}",
            "this step accepts https://github.com/<owner>/<repo>[.git] or git@github.com:<owner>/<repo>[.git]",
        )
    owner, repo = match.group(2), match.group(3).removesuffix(".git")
    if not repo:
        die(f"PUBLIC_TARGET names no repository: {public_target}")
    repo_api = f"{api_base}/repos/{owner}/{repo}"

    # --- the tag and its annotation ----------------------------------------
    tag = argv[0] if argv else ""
    state.tag = tag
    if tag.startswith("-"):
        die(
            f"unknown flag: {tag} — this script takes no flags",
            "omitting CONFIRM_SHA is what makes a run a dry run",
        )
    if not tag:
        tag = state.tag = newest_semver_tag()
        if not tag:
            die("origin carries no strict-semver tag")
    kind = git("cat-file", "-t", f"refs/tags/{tag}", quiet=True)
    if kind.returncode != 0 or kind.stdout.strip() != b"tag":
        die(
            f"{tag} is not an annotated tag in this clone",
            "git fetch origin --tags — the Release body is the tag's annotation",
        )
    # Resolved once; the annotation is read from that id, never the ref again.
    tag_id = state.tag_id = git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").stdout.decode().strip()
    # Everything after the first blank line of the tag object: the header ends
    # there, and what follows is the annotation, kept byte for byte.
    raw = git("cat-file", "tag", tag_id).stdout
    body = raw.split(b"\n\n", 1)[1] if b"\n\n" in raw else b""

    # --- the credential: which variable, never its value -------------------
    if os.environ.get("PROMOTE_TOKEN", ""):
        token, credential_report = os.environ["PROMOTE_TOKEN"], "PROMOTE_TOKEN"
    elif os.environ.get("GITHUB_TOKEN", ""):
        token, credential_report = os.environ["GITHUB_TOKEN"], "GITHUB_TOKEN"
    else:
        token = ""  # nosec B105 # no credential set; a confirmed run refuses
        credential_report = "none — neither PROMOTE_TOKEN nor GITHUB_TOKEN is set, so a confirmed run refuses"

    # --- the report, printed on every run ----------------------------------
    print(f"tag:        {tag}")
    print(f"tag object: {tag_id} — the id CONFIRM_SHA must equal")
    print(f"target:     {public_target}")
    print(f"release:    {repo_api}/releases/tags/{tag}")
    print(f"credential: {credential_report}")
    print(f"body:       the annotation of {tag}, byte for byte, between the markers")
    print("----- begin body -----")
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()
    print("----- end body -----")

    # --- the confirmation must equal the tag object's id -------------------
    confirm = os.environ.get("CONFIRM_SHA", "")
    if not confirm:
        print("dry run: GitHub was not contacted and nothing was created.")
        print(f"to create: CONFIRM_SHA={tag_id} uv run {self_path} {tag}")
        return 0
    if confirm != tag_id:
        die(
            f"CONFIRM_SHA is '{confirm}' but the tag object of {tag} is {tag_id}",
            "the confirmation is the full tag object id — not the tag's name, and not its commit's id",
        )
    state.confirmed = True
    if not token:
        die(
            "neither PROMOTE_TOKEN nor GITHUB_TOKEN is set — no host contacted",
            "one GitHub token with Contents: read and write authorizes both the push and the Release",
        )

    opener = urllib.request.build_opener(NoRedirects)

    def api(method: str, url: str, payload: bytes | None = None) -> tuple:
        """One request → (HTTP status, response body)."""
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=payload, method=method, headers=headers)
        try:
            with opener.open(request) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()
        except urllib.error.URLError as error:
            die(f"could not reach {url}: {error.reason}")
        except Exception as error:
            # The type alone: an exception's text can quote a header value.
            die(f"the request to {url} failed ({type(error).__name__})")

    def fail_http(what: str, status: int, response: bytes):
        err(f"error: {what} returned HTTP {status}")
        sys.stderr.flush()
        sys.stderr.buffer.write(response)
        sys.stderr.buffer.flush()
        err("")
        sys.exit(1)

    # --- an existing Release: identical is success, different refuses -------
    status, response = api("GET", f"{repo_api}/releases/tags/{tag}")
    if status == 200:
        published = field(response, "body").encode("utf-8", "surrogateescape")
        if published == body:
            print(f"ok: the GitHub Release {tag} exists with a body identical to the annotation — nothing written")
            return 0
        err(f"error: the GitHub Release {tag} exists with a different body, and it is left unchanged:")
        sys.stderr.writelines(
            difflib.unified_diff(
                body.decode("utf-8", "surrogateescape").splitlines(keepends=True),
                published.decode("utf-8", "surrogateescape").splitlines(keepends=True),
                fromfile=f"annotation of {tag}",
                tofile=f"Release {tag} on GitHub",
            )
        )
        die(
            "this script never edits a published Release",
            "edit or delete the Release on GitHub if the annotation is what should be published, then re-run",
        )
    if status != 404:
        fail_http(f"reading the Release for {tag}", status, response)

    # --- the tag must already be on the target -----------------------------
    status, response = api("GET", f"{repo_api}/git/ref/tags/{tag}")
    if status == 404:
        die(
            f"{tag} is not on {owner}/{repo} — no Release created",
            "creating one would make GitHub create the tag at the default branch's tip; promote the tag first",
        )
    if status != 200:
        fail_http(f"reading the tag {tag}", status, response)
    # The commit the tag names on the target, sent as target_commitish so that
    # if the tag vanished between this read and the write, GitHub would recreate
    # it at the promoted commit and not at the default branch's tip.
    obj = field(response, "object", "sha")
    if field(response, "object", "type") == "tag":
        status, response = api("GET", f"{repo_api}/git/tags/{obj}")
        if status != 200:
            fail_http(f"reading the tag object {obj}", status, response)
        obj = field(response, "object", "sha")
    if not obj:
        die(f"the target's {tag} names no commit")

    # --- create ------------------------------------------------------------
    # make_latest=legacy lets GitHub's semver and date ordering decide, so a
    # Release backfilled for an older tag leaves the newer one marked latest.
    payload = json.dumps(
        {
            "tag_name": tag,
            "name": tag,
            "body": body.decode("utf-8", "surrogateescape"),
            "target_commitish": obj,
            "make_latest": "legacy",
        }
    ).encode("utf-8")
    status, response = api("POST", f"{repo_api}/releases", payload)
    if status != 201:
        fail_http(f"creating the Release for {tag}", status, response)
    print(f"ok: created the GitHub Release {tag}: {field(response, 'html_url')}")
    return 0


def main(argv: list) -> int:
    if argv[:1] in (["--help"], ["-h"]):
        print(USAGE)
        print()
        print(__doc__.split("\n\n", 1)[0])
        return 0

    state = State()
    try:
        status = run(argv, state)
    except SystemExit as exit:
        status = exit.code if isinstance(exit.code, int) else 1
    except Exception as error:
        # The type alone, never a traceback: it could carry the credential.
        err(f"error: unexpected {type(error).__name__}")
        status = 1
    # Every failure of a confirmed run prints the command that finishes the job
    # by hand. Once promote_cli.py has pushed, re-running the promotion is
    # refused — its new public commit would have the pushed one as its parent,
    # so the tag object differs and the atomic push is rejected — which leaves
    # this command as the only way to create the Release.
    if status != 0 and state.confirmed:
        err(
            "hint: the tag is unaffected. Once the cause above is fixed, create the Release with:",
            f"      CONFIRM_SHA={state.tag_id} PROMOTE_TOKEN=… uv run {sys.argv[0]} {state.tag}",
        )
    return status


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="surrogateescape", line_buffering=True)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    sys.exit(main(sys.argv[1:]))
