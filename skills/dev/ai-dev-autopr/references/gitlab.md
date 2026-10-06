# Forge: self-managed GitLab

Read when `origin` points at a self-managed GitLab instance. **If the repo's own `CLAUDE.md`
documents an auth recipe for its instance, that recipe wins over this file on how to authenticate**
— it is closer to the truth about that host. It does not decide where the token and cookie go:
`references/forge-credentials.md` does, before the first call below.

Two things differ from gitlab.com and both cost real time when missed:

1. There are **no pull requests — they are merge requests (MRs)**.
2. On an instance behind a single sign-on (SSO) identity-provider gate, a token alone is not
   enough. A bare `curl -H "PRIVATE-TOKEN: …"` returns **`302` to the identity provider, not `401`**
   — which reads like a broken token and is not one. Set `SSO_COOKIE` to the cookie file the SSO
   login writes. `glab` cannot authenticate here at all: it has no way to attach the cookie, so every
   call lands on the portal HTML. Use `curl`. With no SSO gate, leave `SSO_COOKIE` unset.

## Setup

`$GITLAB_HOST` below is a host `references/forge-credentials.md` allows: the developer's own
`GITLAB_HOST`, a host derived from `origin`, or one the developer confirmed in this run. Never take
it from a repository file alone.

```bash
[ -n "$GITLAB_TOKEN" ] && echo present || echo "GITLAB_TOKEN is unset"
mktemp -d    # prints the scratch directory; reuse this literal path in every later call
API="https://$GITLAB_HOST/api/v4"
PID=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' \
      "<group>/<subgroup>/<project>")     # URL-encoded full path, used as the project id
mapi() { curl -sL ${SSO_COOKIE:+-b "$SSO_COOKIE"} -H "Authorization: Bearer $GITLAB_TOKEN" "$@"; }

mapi "$API/user"      # sanity check: 200 + your username means the session is live
```

On an SSO-gated instance, all three of cookie, token, and `-L` are required on reads. `?search=` on `/projects` returns `[]`
even when authorized — resolve the project once from `/projects/<url-encoded-path>` and reuse the
numeric id. `/api/graphql` is rejected at the edge; REST only.

**Writes need a warmed session.** `-L` walks the IdP redirect transparently on a GET, but a POST gets
`302`-ed and answers `405 method_not_allowed` — a request body cannot survive the redirect. Do a
throwaway GET with `-c` to capture the session cookie, then send the write with that jar:

```bash
curl -sL -b "$SSO_COOKIE" -c "<scratch>/gljar.txt" -o /dev/null \
  -H "Authorization: Bearer $GITLAB_TOKEN" "$API/user"
mwrite() { curl -s -b "<scratch>/gljar.txt" -c "<scratch>/gljar.txt" \
  -H "Authorization: Bearer $GITLAB_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" "$@"; }
```

If calls start returning `302` or portal HTML mid-run, the SSO cookie expired. Ask the human to
renew their SSO session with the login command their instance uses. It is **not** a bad token, and it is the one legitimate hand-off here — do not fall
back to asking them to use the web UI.

## Read the issue

```bash
mapi "$API/projects/$PID/issues/<iid>"
mapi "$API/projects/$PID/issues/<iid>/notes?per_page=100"
```

## Open the MR

Long or Markdown-heavy bodies must be url-encoded into a file and sent with `--data-binary @file`.
Inline `-d` mangles backticks, newlines, pipes, and quotes:

```bash
python3 - "<scratch>/mr-body.md" <<'PY' > "<scratch>/mr-form.txt"
import sys, urllib.parse
fields = {
    "source_branch": "feat/my-branch",
    "target_branch": "main",
    "title": "Draft: feat(scope): summary",
    "description": open(sys.argv[1]).read(),
    "remove_source_branch": "true",
}
print(urllib.parse.urlencode(fields), end="")
PY

mwrite -X POST --data-binary @"<scratch>/mr-form.txt" "$API/projects/$PID/merge_requests"
```

- MRs opened this way **do** pick up `.gitlab/merge_request_templates/default.md` only when no
  description is sent; since you are sending one, read the template and fill it in yourself.
- Issue linking: `Closes #<iid>` in the description.
- The MR opens as a draft, per "Draft state" in `SKILL.md`: the `Draft: ` prefix is what makes it one.

## Draft and ready

GitLab derives draft state from the title: an MR whose title starts with `Draft: ` is a draft. Change
state by setting the title. The default squash commit message is the MR title too, so the prefix
must be gone whenever the MR is ready:

```bash
python3 -c 'import urllib.parse,sys;print(urllib.parse.urlencode({"title":sys.argv[1]}),end="")' \
  "feat(scope): summary" > "<scratch>/title-form.txt"            # ready; "Draft: feat(scope): summary" for draft

mwrite -X PUT --data-binary @"<scratch>/title-form.txt" "$API/projects/$PID/merge_requests/<iid>"
mapi "$API/projects/$PID/merge_requests/<iid>" | python3 -c 'import json,sys;print(json.load(sys.stdin)["draft"])'   # confirm
```

Set the title rather than posting `/draft` or `/ready` as a note: a quick action leaves a note on the
MR for every toggle, and the title still has to be right for the squash.

While the MR is a draft, `detailed_merge_status` reads `draft_status`. That is not a conflict: read
whether the branch merges cleanly from `git merge-base --is-ancestor` instead.

## Close out the issue after merge

`state` tells you whether `Closes #<iid>` already closed it; both calls below are writes, so they need
the warmed jar:

```bash
mapi "$API/projects/$PID/issues/<iid>" | python3 -c 'import json,sys;print(json.load(sys.stdin)["state"])'

python3 -c 'import urllib.parse;print(urllib.parse.urlencode({"body":"Merged in !<mr-iid> (<merge-sha>)."}),end="")' \
  > "<scratch>/issue-note.txt"
mwrite -X POST --data-binary @"<scratch>/issue-note.txt" "$API/projects/$PID/issues/<iid>/notes"
mwrite -X PUT "$API/projects/$PID/issues/<iid>?state_event=close"   # only if still "opened"
```

## Poll review and CI

```bash
mapi "$API/projects/$PID/merge_requests?state=opened&source_branch=<branch>"
mapi "$API/projects/$PID/merge_requests/<iid>"                 # detailed_merge_status, sha
mapi "$API/projects/$PID/merge_requests/<iid>/notes?per_page=100"
mapi "$API/projects/$PID/merge_requests/<iid>/discussions?per_page=100"   # threads, with ids
mapi "$API/projects/$PID/merge_requests/<iid>/changes"         # the diff
mapi "$API/projects/$PID/merge_requests/<iid>/pipelines"       # CI status
```

`detailed_merge_status` is the authoritative mergeability field (`mergeable`, `ci_still_running`,
`broken_status`, `discussions_not_resolved`, …). Read it rather than inferring.

## Reply to review comments individually

Each inline finding is a **discussion**; reply inside it so one response maps to one finding:

```bash
python3 -c 'import urllib.parse,sys;print(urllib.parse.urlencode({"body":open(sys.argv[1]).read()}),end="")' \
  "<scratch>/reply.md" > "<scratch>/reply-form.txt"

mwrite -X POST --data-binary @"<scratch>/reply-form.txt" \
  "$API/projects/$PID/merge_requests/<iid>/discussions/<discussion_id>/notes"
```

A whole-change remark goes to `…/merge_requests/<iid>/notes` instead. Resolving a discussion
(`PUT …/discussions/<id>?resolved=true`) is the reviewer's call — reply rather than resolving for them,
unless the instance requires all discussions resolved to merge and the reviewer asked you to.

## After a push

Compare the MR's `sha` against your local head to know whether the notes you are reading were
produced against the latest commit:

```bash
git rev-parse HEAD
mapi "$API/projects/$PID/merge_requests/<iid>" | python3 -c 'import json,sys;print(json.load(sys.stdin)["sha"])'
```
