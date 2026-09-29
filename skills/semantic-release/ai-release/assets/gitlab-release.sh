#!/usr/bin/env bash
# Create a GitLab Release object for an existing tag.
# Usage: scripts/gitlab-release.sh <tag> <notes-file>
#
# Why the API rather than the `release:` CI keyword: that keyword is
# implemented by `release-cli`, a Go binary that must be present in the job
# image. The release jobs run on python:3.12-bookworm because they need
# git-cliff, and release-cli is not in it. The REST API needs no extra tooling.
#
# A tag alone is not a release. Bare tags with no Release object and no notes
# are not a substitute for this step.
#
# Runs from CI (CI_JOB_TOKEN, issued automatically) OR from a workstation
# (GITLAB_TOKEN, a personal access token) — a release cut without CI available
# is a supported path, not a partial failure. Credentials are checked BEFORE
# the notes file is even opened, so a workstation run with neither variable set
# fails at the top of this script rather than after release.sh has already
# pushed the tag to origin.

set -euo pipefail

TAG="${1:?usage: gitlab-release.sh <tag> <notes-file>}"
NOTES_FILE="${2:?usage: gitlab-release.sh <tag> <notes-file>}"

# ---------------------------------------------------------------------------
# Credential pre-flight — BEFORE anything is created, and before the notes
# file is read. CI_JOB_TOKEN is preferred (scoped, short-lived, no setup); the
# PRIVATE-TOKEN header with a personal GITLAB_TOKEN is the workstation
# fallback release.sh advertises. Refusing here, rather than letting `curl`
# fail on a request with no auth header, is what keeps the failure from
# landing after the tag is already on origin.
# ---------------------------------------------------------------------------

AUTH_HEADER=""
if [ -n "${CI_JOB_TOKEN:-}" ]; then
  AUTH_HEADER="JOB-TOKEN: $CI_JOB_TOKEN"
elif [ -n "${GITLAB_TOKEN:-}" ]; then
  AUTH_HEADER="PRIVATE-TOKEN: $GITLAB_TOKEN"
else
  echo "error: neither CI_JOB_TOKEN nor GITLAB_TOKEN is set" >&2
  echo "hint: in CI, CI_JOB_TOKEN is issued automatically — this script should" >&2
  echo "      not be run manually in that environment." >&2
  echo "hint: from a workstation, export GITLAB_TOKEN with a personal access" >&2
  echo "      token carrying api scope, then re-run." >&2
  echo "hint: the tag $TAG was pushed successfully by release.sh; only the" >&2
  echo "      Release object is missing. Re-running this script once" >&2
  echo "      credentials are set is safe — it is idempotent." >&2
  exit 1
fi

: "${CI_API_V4_URL:?CI_API_V4_URL is unset — pass it explicitly outside CI, e.g. CI_API_V4_URL=https://<gitlab-host>/api/v4}"
: "${CI_PROJECT_ID:?CI_PROJECT_ID is unset — pass it explicitly outside CI, e.g. CI_PROJECT_ID=<project-id>}"

if [ ! -f "$NOTES_FILE" ]; then
  echo "error: notes file not found: $NOTES_FILE" >&2
  exit 1
fi

# Build the JSON body with python rather than string interpolation: the notes
# contain newlines, backticks, quotes, and asterisks, all of which need
# escaping.
PAYLOAD=$(TAG="$TAG" NOTES_FILE="$NOTES_FILE" python3 -c '
import json, os
with open(os.environ["NOTES_FILE"], encoding="utf-8") as fh:
    description = fh.read()
print(json.dumps({"name": os.environ["TAG"], "tag_name": os.environ["TAG"], "description": description}))
')

# Buffer the response body in a file mktemp creates, never at a fixed path.
# Two defects come with a predictable name on a shared host: `curl --output`
# opens whatever is already there and follows a symlink, so another local user
# can pre-empt the path and redirect the write; and nothing ever deletes it, so
# a body that on failure echoes request detail back is left readable on disk.
# mktemp creates the file itself, 0600 and unguessable, and the trap removes it
# on every exit path this script has — including a `set -e` abort. Allocated
# here, after every refusal above, so a run that refuses still creates nothing.
RESPONSE_FILE=$(mktemp)
trap 'rm -f "$RESPONSE_FILE"' EXIT

HTTP_CODE=$(printf '%s' "$PAYLOAD" | curl --silent --show-error \
  --output "$RESPONSE_FILE" \
  --write-out '%{http_code}' \
  --request POST \
  --header "$AUTH_HEADER" \
  --header "Content-Type: application/json" \
  --data-binary @- \
  "$CI_API_V4_URL/projects/$CI_PROJECT_ID/releases")

if [ "$HTTP_CODE" = "201" ]; then
  echo "ok: created GitLab Release $TAG"
elif [ "$HTTP_CODE" = "409" ]; then
  # Idempotent: a Release for this tag already exists. Not a failure — the tag
  # is pushed and the Release is present, which is the desired end state.
  echo "ok: GitLab Release $TAG already exists"
else
  echo "error: failed to create GitLab Release $TAG (HTTP $HTTP_CODE)" >&2
  cat "$RESPONSE_FILE" >&2
  echo >&2
  echo "hint: the tag was pushed successfully — only the Release object" >&2
  echo "      failed. Re-running this script is safe; it is idempotent." >&2
  exit 1
fi
