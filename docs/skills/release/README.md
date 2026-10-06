---
title: "release"
sidebar_label: "release"
sidebar_position: 6
---

# `release`

One skill that configures how a repository releases — internally, and on request publicly. It
activates from its slash command or from a request matching its description.

| Skill | What it does |
|---|---|
| [`ai-scaffold-release`](./ai-scaffold-release/) | configures the internal release path — version derivation, git-cliff config, release and forge-release scripts, CI jobs, bootstrap tag — and, only when publishing is what was asked for, a promote path that publishes one tag's filtered tree to a public target |

## Commit conventions

Commit subjects follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
Release notes and the next version are both derived from those subjects by
[git-cliff](https://git-cliff.org/), and versions follow [Semantic Versioning](https://semver.org/).
There is no changelog file and no version file: the commit subject is the only record of a change.

`ai-scaffold-release` installs this convention into a repository. Its type table, which maps each
type to a release-notes section and a version bump, is in the skill's
`references/commit-convention.md`.

### Where this differs from the specifications

- `style`, `test`, and `chore` are skipped. They appear in no release-notes section and bump no
  version.
- A subject with an unrecognized type is kept rather than filtered out. It bumps the patch version
  and appears in no section, so the version moves with nothing in the notes to explain it.
- Before `1.0.0`, a breaking change (`feat!:` or a `BREAKING CHANGE:` footer) bumps the minor
  version, not the major.
- Nothing checks a subject when it is committed. A malformed subject is found at release time, when
  it can be fixed only by rewriting history.
