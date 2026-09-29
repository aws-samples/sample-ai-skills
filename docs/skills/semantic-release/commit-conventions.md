---
title: "Commit Conventions"
sidebar_label: "Commit Conventions"
sidebar_position: 2
---

# Commit Conventions

This repository uses **Conventional Commits** — a commit message format where the subject line
starts with a type that machines can parse. The format is not cosmetic: `cliff.toml` sets
`conventional_commits = true`, and the release workflow generates the release notes for a tag by
parsing commit subjects. This project keeps no `CHANGELOG.md` — the commit subject is the only
place a change is described, so a malformed subject lands in the wrong section of the notes, or
creates a bogus one, with no hand-written file to compensate.

```
<type>(<optional-scope>): <subject>

<body>

<optional-footer>
```

## Types

Only these types are mapped in `cliff.toml`. Anything else is not recognized.

| Type | Release-notes section | Use for |
|---|---|---|
| `feat` | Added | New skills or capabilities |
| `fix` | Fixed | Corrections to existing behavior |
| `doc` / `docs` | Documentation | Documentation-only changes |
| `perf` | Performance | Performance improvements |
| `refactor` | Changed | Restructuring without behavior change |
| `ci` | CI/Build | Pipeline, jobs, release automation |
| `build` | CI/Build | Build backend, packaging, dependencies |
| `revert` | Reverted | Reverting an earlier commit |
| `style` | *(skipped)* | Formatting, whitespace, no logic change |
| `test` | *(skipped)* | Test additions or corrections |
| `chore` | *(skipped)* | Tooling, housekeeping |

`style`, `test`, and `chore` are **skipped**: they appear in no section *and* derive no version
change — no bump, no notes. The previous configuration instead gave each of them a section of its
own (`Styling`, `Testing`, `Miscellaneous`), so housekeeping showed up in release notes as though it
were a change worth reading about. A separate `chore(release)` skip is no longer needed now that
`^chore` is skipped outright.

Add `!` before the colon for a breaking change: `feat(installer)!: drop Python 3.9 support`.

## Scopes

The scope is optional and free-form; git-cliff renders it in italics after the subject. Use the area
of the repository the change touches — `skills`, `installer`, `docs`, `ci`, `cli`.

## Subject and body

- **Subject** — imperative mood ("add", not "added" or "adds"), lowercase after the colon, no
  trailing period, 72 characters or fewer.
- **Body** — optional but expected for anything non-trivial. Wrap at ~72 columns. Explain **what
  changed and why**, including consequences and deliberate non-goals. Thorough bodies are the house
  style here; `git show 2f1b63c` is a representative example.
- **The body's first paragraph is published.** Release notes carry each subject followed by the
  paragraph up to the first blank line, and nothing after it — so open with a paragraph that stands
  on its own as the summary of the change, and put the detail, the measurements, and the rejected
  alternatives below it. Everything after that blank line stays in the commit, one `git show <sha>`
  away, rather than in the notes. Writing thoroughly still pays; it just pays in the history.

```
feat(skills): prefix work folders with their creation date

Every folder created under the working root is now named
YYYY-MM-DD-<inferred-name>. The date comes from `date +%F` rather than
model recall, is written once at creation, and is never rewritten.

Existing folders are not renamed. No migration is performed or required.
```

## Guidance for AI coding agents

Agents (Claude Code, Kiro) commit to this repository, so consistency depends on following the same
rules a human would:

- **Never use a type outside the table above.** Nothing filters an unrecognized one out. `cliff.toml`
  sets `filter_unconventional = false`, so a subject matching no parser is kept: it derives a **patch
  bump** and lands in **no section at all**. A version therefore moves with nothing published to
  explain it. The release path refuses when *every* commit in the window is like that (see
  the repository's release procedure), but one bad subject among ten good ones is simply invisible.
  The junk `### Update` section that the 48 legacy subjects used to produce is now suppressed by an
  explicit `^Update:` skip parser rather than by luck.
- **Do not imitate the existing history.** 48 commits use a generated `Update: add N file(s),
  modify M file(s)` form that predates this convention. They are legacy, not a pattern to match.
- **Never add attribution trailers** — no `Co-Authored-By:`, no "Generated with Claude Code". The
  history contains none.
- **Describe intent, not the diff.** `fix(installer): skip dot-prefixed skill directories` is
  useful; `modify 2 file(s)` is not. The subject is what a reader sees in the release notes.
- **One logical change per commit.** When a change spans both runtimes (`.claude/skills/` and
  `.kiro/skills/`), that is still one logical change and belongs in one commit.
- **Do not run `make release` as part of ordinary work, and do not add a `CHANGELOG.md`.** Cutting a
  release is a deliberate act, not a side effect of a code change — see
  the repository's release procedure. `make release-preview` is safe: it creates nothing. There is no
  version to bump by hand and no file holding one; both the changelog and the `VERSION` file were
  removed on purpose, because a second hand-maintained copy of something derived only drifts from it.

## The subject decides the version, not just the section

`git-cliff --bumped-version` computes the next release from these same subjects, and nothing else
supplies a version. So the type you choose does two jobs:

| Subject | Section | Version effect |
|---|---|---|
| `feat: …` | Added | minor bump (`0.3.0` → `0.4.0`) |
| `fix:`, `perf:`, `refactor:`, `ci:`, `build:`, `revert:`, `docs:` | as tabled above | patch bump |
| `chore:`, `style:`, `test:` | none | **no bump** |
| anything unrecognized | none | patch bump — the version moves with nothing published to explain it |
| `feat!:` or a `BREAKING CHANGE:` footer | Added | pre-1.0, still a minor bump: `breaking_always_bump_major = false` keeps derivation from stumbling into `1.0.0` |

A release consisting only of `chore:`/`style:`/`test:` commits derives no new version at all, and the
release path reports that there is nothing to release and exits successfully.

## Where this is enforced

Nothing validates a commit subject at commit time — there is no hook, and no CI job lints one. That is
a decision rather than an omission: 48 of the roughly 80 subjects already in this history would fail
such a check. The format matters at release, when `git-cliff` parses the accumulated history, so a bad
subject is discovered long after it is written and can only be fixed by rewriting history. The one
place an omission is noticeable is the `gitlab:release:preview` job, and reading it is voluntary.
Getting it right when you commit is the whole control.

For the branching model and merge request process these commits land in, see the
repository's contributing guidance.
