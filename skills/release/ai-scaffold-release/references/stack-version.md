# Stack and pinned versions

Tooling this skill's templates assume, and why each pin exists.

## `git-cliff` 2.10.1

Every rendering behavior this skill's `assets/cliff.toml` depends on —
`trim = false` preserving nested indentation, the `^docs?` parser grouping
both singular and plural doc commits, `--strip all` removing header/footer —
is verified specifically against this version. `assets/release_cli.py` declares
`git-cliff==2.10.1` in its PEP 723 inline metadata, so every `uv run` of it — in
CI or on a workstation — resolves this version and runs the `git-cliff` binary
installed into the script's own environment, never one found on `PATH`. A newer
release changing template-rendering defaults would not fail loudly, it would
render differently.

## `uv` 0.12.19

Every bundled script runs as `uv run scripts/<name>_cli.py`, and `uv` is the
only thing a consumer installs to run them: it fetches Python 3.14 and the
script's declared dependencies itself. `assets/gitlab-ci-release.yml` and
`assets/gitlab-ci-promote.yml` install it with `pip install 'uv==0.12.19'`, and
`assets/github-release.yml` with `astral-sh/setup-uv` given `version: "0.12.19"`,
so a CI run uses the version this skill's tests ran under.

## `actions/checkout` 4.4.0

`assets/github-release.yml` pins its checkout step to the full commit SHA
`11d5960a326750d5838078e36cf38b85af677262` — v4.4.0 — rather than the `v4`
tag. A tag or branch ref can be silently repointed by the action owner, which
is how the trivy-action and kics-github-action compromises reached downstream
workflows; this template is installed into consumer repositories, so that is
their exposure and not only ours. This skill's own test suite asserts that every
`uses:` in the template carries a 40-character SHA, so a bump must replace the
SHA and the trailing `# v…` comment together.

The pin stays on the v4 line deliberately. `actions/checkout` has since
released v5, v6 and v7; only `fetch-depth: 0` is used here, so a major bump
buys nothing this template needs while changing the runner's Node version
under it.

## Why the templates pin less tightly than this repository does

`actions/checkout` above is the exception. The templates otherwise name their
inputs by mutable reference — `assets/gitlab-ci-release.yml` runs
`public.ecr.aws/docker/library/python:3.12-bookworm`, a tag, and both templates
install `uv` by version rather than by artifact hash. The repository that
*ships* them does neither: its own `.gitlab-ci.yml` pins the job image by
`@sha256:` digest and installs `uv` from `ci/requirements-unit.txt` under
`pip install --require-hashes`.

That asymmetry is deliberate, and it is the opposite of what it looks like. A
digest baked into a template consumers copy is a digest nobody will ever bump:
the consumer does not know it is there, and this skill has no update path into an
already-installed copy. The template would hand every consumer a pin that is
correct on installation day and progressively staler forever after — arguably
worse than the tag, which at least tracks upstream security rebuilds. A pin is
only a security improvement for someone who owns the refresh.

So the pinning burden sits where the refresh can actually happen. If a consumer
wants their release pipeline pinned, the right shape is instructional — resolve a
digest for *their* repository, with a command they own — not a literal this skill
bakes in. Until that exists, a consumer installing these templates inherits the
mutable references, and that is their exposure to accept.

## Python

Every bundled script declares `requires-python = ">=3.14,<3.15"`, and `uv`
provides that interpreter whatever Python the machine or the CI image has. Only
`assets/release_cli.py` declares a third-party dependency, `git-cliff`; the
others use the standard library alone. `assets/gitlab_release_cli.py` builds its
JSON payload with `json.dumps` rather than string interpolation, because release
notes contain newlines, backticks, quotes, and asterisks that would otherwise
need hand-rolled escaping.

## Forge CLIs

`assets/github-release.yml` uses `gh release create`, relying on the GitHub
CLI preinstalled on `ubuntu-latest` GitHub-hosted runners, and its
`--notes-from-tag` flag, which needs `gh` 2.79.0 or later.
`assets/gitlab_release_cli.py` calls the GitLab REST API directly rather than
through `release-cli`, because that binary is not present in the
`python:3.12-bookworm` image the GitLab jobs run under and adding it would be a
second dependency for what one HTTP request already does.
