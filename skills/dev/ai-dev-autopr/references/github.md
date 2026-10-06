# Forge: GitHub

Read when `origin` points at `github.com`. Commands use `gh`; every one takes `--repo <owner>/<repo>`
so they work from a worktree without relying on the inferred repo.

`gh` sends its token to `github.com`, or to the host `GH_HOST` or `--hostname` names. Give either
only a host `references/forge-credentials.md` allows, and apply that file before the first call
below.

## Preflight

```bash
gh auth status                     # if gh is absent, GITHUB_TOKEN must be exported
mktemp -d                          # prints the scratch directory; reuse this literal path in every later call
gh api user --jq .login            # who you are
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name   # base branch
```

If `gh` is unavailable, fall back to `curl` with `Authorization: Bearer $GITHUB_TOKEN` against
`https://api.github.com` — do not stop.

## Read the issue

```bash
gh issue view <n> --repo <owner>/<repo> --json title,body,labels,comments
```

For a URL, parse owner/repo/number out of it rather than assuming the current repo.

## Open the PR

```bash
gh pr create --repo <owner>/<repo> --draft \
  --base <base> --head <branch> \
  --title "feat(scope): summary" \
  --body-file "<scratch>/pr-body.md"
```

- The body file gets `Closes #<n>` (or `Fixes`) for issue linking — GitHub only auto-closes on those
  keywords, and only from the default branch.
- `.github/pull_request_template.md` is **not** applied when `--body-file` is given: read it and fill
  it in yourself.
- The PR opens as a draft, per "Draft state" in `SKILL.md`. GitHub offers drafts on private
  repositories only on some plans; if `--draft` is refused, open without it and follow that
  section's rule for a forge without drafts.

## Draft and ready

```bash
gh pr ready <n> --repo <owner>/<repo>                               # mark ready, before each review wait
gh pr ready <n> --repo <owner>/<repo> --undo                        # return to draft, before each push
gh pr view <n> --repo <owner>/<repo> --json isDraft --jq .isDraft   # confirm after either
```

Most review bots skip drafts. Marking a draft ready emits a `ready_for_review` event, which many of
them start a review on — so marking ready is what requests each round's review.

While the PR is a draft, `mergeStateStatus` reads `DRAFT`. That is not a conflict: read whether the
branch merges cleanly from `git merge-base --is-ancestor` instead.

## Close out the issue after merge

```bash
gh issue view <n> --repo <owner>/<repo> --json state,stateReason   # already closed by `Closes #<n>`?
gh issue close <n> --repo <owner>/<repo> \
  --comment "Merged in #<pr> (<merge-sha>)."                       # only if still OPEN
gh issue comment <n> --repo <owner>/<repo> --body-file "<scratch>/note.md"  # left open on purpose
```

## Poll review and CI

```bash
gh pr view <n> --repo <owner>/<repo> --json state,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
gh api "repos/<owner>/<repo>/pulls/<n>/reviews"  --paginate   # review verdicts + bodies
gh api "repos/<owner>/<repo>/pulls/<n>/comments" --paginate   # inline review comments (the threads)
gh pr checks <n> --repo <owner>/<repo>                        # required-check status
```

`mergeStateStatus` of `BLOCKED` / `DIRTY` / `BEHIND` each mean a different fix (missing approval,
conflict, stale base) — read it rather than guessing.

## Reply to review comments individually

Reply **in the thread**, keyed by the comment id, so each finding gets its own response:

```bash
gh api -X POST "repos/<owner>/<repo>/pulls/<n>/comments/<comment_id>/replies" \
  -f body="$(cat "<scratch>/reply.md")"
```

Resolving a thread requires GraphQL (`resolveReviewThread`) and is the reviewer's prerogative — reply
rather than resolving on their behalf.

For something that spans the whole change, one top-level comment is fine:

```bash
gh pr comment <n> --repo <owner>/<repo> --body-file "<scratch>/summary.md"
```

## After a push

Bots re-review on push. Re-fetch reviews and checks; `headRefOid` tells you whether what you are
reading was produced against your latest commit:

```bash
gh pr view <n> --repo <owner>/<repo> --json headRefOid
```
