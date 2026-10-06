# Tracker: GitLab Issues (gitlab.com or self-managed)

Read when `origin` points at a GitLab instance. **If the repo's own `CLAUDE.md` documents an auth
recipe for its instance, that recipe wins over this file on how to authenticate** — it is closer to
the truth about that host. It does not decide where the token and cookie go:
`references/forge-credentials.md` does, before the first call below.

On an instance behind a single sign-on (SSO) identity-provider gate, a token alone is not enough:
a bare `curl -H "PRIVATE-TOKEN: …"` returns **`302` to the identity provider, not `401`** — which
reads like a broken token and is not one. Set `SSO_COOKIE` to the cookie file the SSO login writes.
`glab` cannot authenticate there at all (no way to attach the cookie), so use `curl`. On gitlab.com,
leave `SSO_COOKIE` unset and use `glab` or plain `curl` with the token.

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

mapi "$API/user"                                      # 200 + your username = live session
mapi "$API/projects/$PID" | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["id"], d["issues_enabled"])'
```

On an SSO-gated instance, cookie, token, and `-L` are all required on reads. `?search=` on `/projects` returns `[]` even when
authorized — resolve the project once from `/projects/<url-encoded-path>` and reuse the numeric id.
`/api/graphql` is rejected at the edge; REST only.

**Writes need a warmed session.** `-L` walks the IdP redirect on a GET, but a POST gets `302`-ed and
answers `405 method_not_allowed` — a request body cannot survive the redirect. Warm a jar first:

```bash
curl -sL -b "$SSO_COOKIE" -c "<scratch>/gljar.txt" -o /dev/null \
  -H "Authorization: Bearer $GITLAB_TOKEN" "$API/user"
mwrite() { curl -s -b "<scratch>/gljar.txt" -c "<scratch>/gljar.txt" \
  -H "Authorization: Bearer $GITLAB_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" "$@"; }
```

`302` or portal HTML mid-run means the SSO cookie expired. Ask the human to renew their SSO session
with the login command their instance uses — it is not a bad token, and it is the one legitimate
hand-off. Do not fall back to "use the web UI".

## Harvest the conventions

```bash
ls .gitlab/issue_templates/ 2>/dev/null                 # Bug.md, Feature.md, … (repo-side)
mapi "$API/projects/$PID/labels?per_page=100" | python3 -c 'import json,sys;[print(l["name"]) for l in json.load(sys.stdin)]'
mapi "$API/projects/$PID/issues?state=opened&per_page=10" | \
  python3 -c 'import json,sys;[print(i["iid"], i["issue_type"], i["title"]) for i in json.load(sys.stdin)]'
```

A template is applied **only** when no `description` is sent. You are sending one, so read the
matching template file and fill it in yourself, keeping its headings intact.

`issue_type` is a first-class field: `issue` (default), `incident` (live, user-affecting — pages
whoever is on call, so use it deliberately), `task`, `test_case`.

## Check for duplicates

```bash
mapi "$API/projects/$PID/issues?state=opened&search=<keywords>&in=title,description" | \
  python3 -c 'import json,sys;[print(i["iid"], i["title"], i["web_url"]) for i in json.load(sys.stdin)]'
```

## Create it

Markdown-heavy bodies must be url-encoded into a file and sent with `--data-binary @file`; inline
`-d` mangles backticks, newlines, pipes, and quotes.

```bash
python3 - "<scratch>/issue-body.md" <<'PY' > "<scratch>/issue-form.txt"
import sys, urllib.parse
fields = {
    "title": "Policy search returns no results when the policy number contains a hyphen",
    "description": open(sys.argv[1]).read(),
    "issue_type": "issue",
    "labels": "bug,area::backend",          # comma-separated, existing labels only
}
print(urllib.parse.urlencode(fields), end="")
PY

mwrite -X POST --data-binary @"<scratch>/issue-form.txt" "$API/projects/$PID/issues" | \
  python3 -c 'import json,sys;d=json.load(sys.stdin);print(d["iid"], d["web_url"])'
```

Unknown label names are **created silently** by GitLab rather than rejected, which is how label lists
rot — apply only names from the labels call above.

Optional, and only when the project uses them: `assignee_ids`, `milestone_id`, `due_date`,
`confidential=true` (use it for anything security-sensitive on a broadly readable instance).

## Cross-link siblings

```bash
python3 -c 'import urllib.parse;print(urllib.parse.urlencode({"body":"Filed alongside #<a> and #<b> from the same report."}),end="")' \
  > "<scratch>/note.txt"
mwrite -X POST --data-binary @"<scratch>/note.txt" "$API/projects/$PID/issues/<iid>/notes"
```

`/issues/<iid>/links` creates a typed relation (`relates_to`, `blocks`) when the instance supports it;
a note is the portable fallback.

## Add evidence to an existing issue instead

Same `notes` endpoint as above, with the new evidence as the body. Comment only when you have
something the issue does not already say.
