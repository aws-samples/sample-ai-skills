# Forge topologies

What the probe step reads before asking anything, and which machinery variant
each topology installs.

## Detecting the forge

Read `git remote get-url origin` (fall back to any other configured remote if
`origin` is absent — report which one). Apply these rules in order; the first
that holds decides:

- The remote host contains `github.com` → **GitHub**. Installs
  `assets/github-release.yml` as `.github/workflows/release.yml`. No
  `gitlab-release.sh` counterpart is installed — `scripts/release.sh` skips
  forge-release-object creation and the workflow itself runs
  `gh release create` after the script returns.
- The remote host contains `gitlab`, **or** a `.gitlab-ci.yml` exists at the
  repository root → **GitLab**. Installs `assets/gitlab-ci-release.yml` as a
  section merged into the repository's `.gitlab-ci.yml`, plus
  `scripts/gitlab-release.sh`. The file check is what classifies a
  self-managed instance whose hostname does not contain `gitlab`.
- Anything else → report the origin URL and ask the builder which forge to
  target rather than guessing; an unrecognized host is not evidence of either
  topology. A self-managed GitLab with no `.gitlab-ci.yml` yet lands here.

## What "merged into .gitlab-ci.yml" means

If `.gitlab-ci.yml` does not exist, write the release section as the whole
file. If it exists, append the release jobs and the `.release-base` template
without disturbing existing stages, jobs, or `include:` blocks — report the
diff before writing rather than overwriting silently. Add `release` to the
`stages:` list if that list exists and does not already contain it.

## What the probe reports before asking

- Forge type and origin URL (this section)
- Tag count and, if any exist, whether the newest matches the release tag
  pattern (`gitlab-release.sh`/`github-release.yml`'s `v[0-9]+.[0-9]+.[0-9]+`)
- Which of the five machinery files already exist at the repository root
- The proportion of existing commit subjects the parser table in
  `references/commit-convention.md` would group versus skip versus leave
  unmatched

This report is what the three questions (see `SKILL.md`) are asked against —
the builder answers only what the probe could not determine on its own.
