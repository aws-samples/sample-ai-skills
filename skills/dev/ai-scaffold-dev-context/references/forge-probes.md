# Forge Probes

The forge reads this skill may make, per command-line tool, and the machine check. Every call here is a read. Never pass a method flag (`-X`, `--method`), a request body (`-f`, `-F`, `--input`), or a subcommand that creates, edits, closes, or deletes anything.

A probe is evidence only when it succeeds. When the tool is missing, unauthenticated, or the call fails, the fact it would have settled stays undetected: name the call that failed in the report, and settle the fact by asking.

## GitHub — `gh`

`<owner>/<repo>` is the recorded or detected `project`.

| Fact | Call | Read |
|---|---|---|
| visibility, for exposure | `gh repo view <owner>/<repo> --json visibility` | `PUBLIC` → the project is publicly visible |
| base branch, when `refs/remotes/origin/HEAD` is unset | `gh repo view <owner>/<repo> --json defaultBranchRef` | `defaultBranchRef.name` |
| tracker | `gh repo view <owner>/<repo> --json hasIssuesEnabled` | `true` → the forge tracks issues |
| reviewer | `gh pr list --repo <owner>/<repo> --state merged --limit 3 --json number`, then `gh api repos/<owner>/<repo>/pulls/<number>/reviews` for each | a review whose `user.type` is `Bot` names an automated reviewer |

GitHub has no numeric project id that this block uses: record `project_id: none`.

## GitLab — `glab`

Pass `--hostname <web_host>` on every call, so a host that differs from the SSH host is the one asked. `<path>` is the `project` with every `/` encoded as `%2F`.

| Fact | Call | Read |
|---|---|---|
| project id | `glab api --hostname <web_host> projects/<path>` | `id` |
| visibility, for exposure | the same response | `visibility` is `public` → the project is publicly visible |
| base branch, when `refs/remotes/origin/HEAD` is unset | the same response | `default_branch` |
| tracker | the same response | `issues_enabled` is `true` → the forge tracks issues |
| reviewer | `glab api --hostname <web_host> "projects/<id>/merge_requests?state=merged&per_page=3"`, then `glab api --hostname <web_host> projects/<id>/merge_requests/<iid>/notes` for each, then `glab api --hostname <web_host> users/<author.id>` for each distinct non-system note author | a user whose `bot` is `true` names an automated reviewer. A note's own `author` carries no `bot` field, so read it from the user. |

## The machine check

Run after the facts are settled, for the `cli` and `web_host` this run resolved. It reports and records nothing.

| Check | Command | Result |
|---|---|---|
| installed | `command -v <cli>` | no output → **missing**. Report how to install it, and skip the next row. |
| authenticated | `gh auth status --hostname <web_host>`, or `glab auth status --hostname <web_host>` | a non-zero exit → **installed, unauthenticated for `<web_host>`**. Report `<cli> auth login --hostname <web_host>` as the step that closes it. |

Missing and unauthenticated are different gaps with different fixes, so report them in different words. Do not read, print, or record which authentication method, token, or credential variable the tool uses.
