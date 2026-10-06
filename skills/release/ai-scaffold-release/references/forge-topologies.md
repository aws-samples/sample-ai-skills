# Forge topologies

What the probe step reads before asking anything, and which machinery variant
each topology installs.

## Detecting the forge

Read `git remote get-url origin` (fall back to any other configured remote if
`origin` is absent — report which one).

First read the development-context block in the root `AGENTS.md` or
`CLAUDE.md`, per `references/dev-context.md`, for its forge, access, and
exposure groups. When it records a resolved `forge`, and that agrees with the
live `origin` as that reference defines — its hosts and project match the URL,
and the rules below name the same forge or none — use the recorded forge
without asking. A block recording `gitlab` for a matching `origin` therefore
classifies a self-managed instance that has no `.gitlab-ci.yml` yet. When the
rules below name a different forge, use theirs and say in one line that the
recorded forge is stale.

Otherwise apply these rules in order; the first that holds decides:

- The remote host contains `github.com` → **GitHub**. Installs
  `assets/github-release.yml` as `.github/workflows/release.yml`. No
  `gitlab_release_cli.py` counterpart is installed — `scripts/release_cli.py` skips
  forge-release-object creation and the workflow itself runs
  `gh release create` after the script returns.
- The remote host contains `gitlab`, **or** a `.gitlab-ci.yml` exists at the
  repository root → **GitLab**. Installs `assets/gitlab-ci-release.yml` as a
  section merged into the repository's `.gitlab-ci.yml`, plus
  `scripts/gitlab_release_cli.py`. The file check is what classifies a
  self-managed instance whose hostname does not contain `gitlab`.
- Anything else → report the origin URL and ask the builder which forge to
  target rather than guessing; an unrecognized host is not evidence of either
  topology. A self-managed GitLab with no `.gitlab-ci.yml` yet lands here.

## Classifying the promote target

The promote path classifies `PUBLIC_TARGET` with the first rule above, applied
to the target's host rather than to `origin`'s. The second rule's file check
reads this repository's tree and says nothing about a target, so a target is
GitHub or it is not. The skill states the classification and asks the builder
to confirm it before installing anything for it.

- The target's host contains `github.com` → **GitHub**. The promote job is
  merged in its `.promote-form-github` form: the push credential is an HTTPS
  token, `PROMOTE_TOKEN`, stored in a credential-helper file and never in a URL,
  and a second script line runs `scripts/github_release_cli.py` after the push to
  create the Release a pushed tag does not get. That script accepts only
  `https://github.com/<owner>/<repo>[.git]` and
  `git@github.com:<owner>/<repo>[.git]`, and refuses any other value, naming it,
  before it contacts a host. A host the rule matched that is not `github.com`
  itself is therefore refused at the first dry run.
- Anything else → the `.promote-form-ssh` form: a deploy key over SSH, and no
  Release step, which is installed for GitHub alone.

## What "merged into .gitlab-ci.yml" means

If `.gitlab-ci.yml` does not exist, write the release section as the whole
file. If it exists, append the release jobs and the `.release-base` template
without disturbing existing stages, jobs, or `include:` blocks — report the
diff before writing rather than overwriting silently. Add `release` to the
`stages:` list if that list exists and does not already contain it.

## What the probe reports before asking

- Forge type and origin URL (this section), and whether the forge came from
  the development-context block, with its `recorded` date
- Exposure and the public target, from the block and `.promote-target`, taking
  the more public of the two as `references/dev-context.md` says
- Tag count and, if any exist, whether the newest matches the release tag
  pattern (`gitlab_release_cli.py`/`github-release.yml`'s `v[0-9]+.[0-9]+.[0-9]+`)
- Which of the five machinery files already exist at the repository root
- The proportion of existing commit subjects the parser table in
  `references/commit-convention.md` would group versus skip versus leave
  unmatched

This report is what the three questions (see `SKILL.md`) are asked against —
the builder answers only what the probe could not determine on its own.
