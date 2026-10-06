# Tracker: GitHub Issues

Read when `origin` points at `github.com`. Every command takes `--repo <owner>/<repo>` so it works
from a worktree without relying on inference.

`gh` sends its token to `github.com`, or to the host `GH_HOST` or `--hostname` names. Give either
only a host `references/forge-credentials.md` allows, and apply that file before the first call
below.

## Preflight

```bash
gh auth status                                          # absent? GITHUB_TOKEN must be exported
mktemp -d                                               # prints the scratch directory; reuse this literal path in every later call
gh repo view --repo <owner>/<repo> --json hasIssuesEnabled,url --jq .
```

`hasIssuesEnabled: false` means this repo does not take issues — check whether the org routes them to
another repo (`CONTRIBUTING.md` usually says), and fall back to the local file if not.

If `gh` is unavailable, use `curl` with `Authorization: Bearer $GITHUB_TOKEN` against
`https://api.github.com` rather than stopping.

## Harvest the conventions

```bash
ls .github/ISSUE_TEMPLATE/ 2>/dev/null                  # per-kind templates (md or yml forms)
cat .github/ISSUE_TEMPLATE/config.yml 2>/dev/null       # blank_issues_enabled, contact links
gh label list --repo <owner>/<repo> --limit 100         # the only labels you may apply
gh issue list --repo <owner>/<repo> --limit 10 --json number,title,labels   # house title style
```

A `.yml` issue **form** declares required fields (`validations: required: true`) and fixed labels.
`gh issue create --body` bypasses the form entirely, so read the form and satisfy every required
field as a markdown section with the same heading — otherwise triage automation keyed on those
headings misses this issue.

Issue **types** (org-level: Bug / Feature / Task) are separate from labels:

```bash
gh api "repos/<owner>/<repo>/issues/1" --jq .type       # is the repo using types at all?
```

## Check for duplicates

```bash
gh issue list --repo <owner>/<repo> --state open --search "<distinctive keywords>" \
  --json number,title,url
gh search issues --repo <owner>/<repo> --state open "<error string>" --json number,title,url
```

Search the distinctive error text and the affected file path, not your own paraphrase.

## Create it

```bash
gh issue create --repo <owner>/<repo> \
  --title "Policy search returns no results when the policy number contains a hyphen" \
  --body-file "<scratch>/issue-body.md" \
  --label bug --label area/backend
```

- Always `--body-file`; an inline `--body` mangles backticks, newlines, and quotes.
- `--label` fails the whole call on an unknown label. Apply only labels from `gh label list`.
- Optional and only when the project actually uses them: `--assignee`, `--milestone`, `--project`.
- Set an issue type after creation (no `gh issue create` flag for it):
  ```bash
  gh api -X PATCH "repos/<owner>/<repo>/issues/<n>" -f type=Bug
  ```

The command prints the issue URL — report it verbatim.

## Cross-link siblings

After creating a split batch, tie them together:

```bash
gh issue comment <n> --repo <owner>/<repo> \
  --body "Filed alongside #<a> and #<b> from the same report."
```

## Add evidence to an existing issue instead

When the duplicate search found the issue already open:

```bash
gh issue comment <n> --repo <owner>/<repo> --body-file "<scratch>/new-evidence.md"
```

Comment only if you have something new — a sharper repro, another affected path, a root cause.
Restating the existing issue adds noise.
