---
title: "ai-scaffold-docusaurus-site"
sidebar_label: "ai-scaffold-docusaurus-site"
sidebar_position: 3
---

# `ai-scaffold-docusaurus-site`

| | |
|---|---|
| Invoke | `/ai-scaffold-docusaurus-site [--headless]` |
| Activation | slash command only — never from intent, keywords, or near-synonyms |
| Domain | [software-docs](../) |
| Source | `skills/software-docs/ai-scaffold-docusaurus-site/SKILL.md` |
| Effort | `medium` |

## Overview

The skill stands up a Docusaurus 3 site in the repository it is run in. It writes the site's build
files, and the empty content directories the chosen layout needs, each seeded with a `README.md`
index page. It writes no content page. It then installs and builds the site, and reports it verified
only when the build produced one page for every index page it seeded.

Navigation is derived from the tree. Each top-level directory of the content root gets its own
sidebar and navbar item when the site loads its configuration, labelled and ordered by that
directory's `README.md` frontmatter. Adding an audience or a section later is therefore a directory,
not a configuration edit.

## Arguments

| Argument | Effect |
|---|---|
| `--headless` | Ask nothing. Take the recommended option of every question and mark each such answer as inferred in the report. |

## Interview

| Question | Options | Recommended |
|---|---|---|
| Layout | *split*: site in `internal/docs/`, pages in `docs/`. *single*: site in `docs/`, pages in `docs/docs/` | split |
| Audiences | none; `users` and `developers`; a list the user names | none |
| Title | any title without `'`, `"`, `\`, a backtick, or `__` | the repository directory's name |
| Maintainer-only audience | none, or one declared audience, placed at `docs/internal/`. Asked only under split with audiences | none |

An audience name must be lowercase letters, digits, and hyphens, and must not be `internal` or
`working`. A name that breaks the rule is asked again, never rewritten.

## What it writes

| Path | From |
|---|---|
| `<site>/docusaurus.config.ts`, `site.ts`, `sidebars.ts` | the site configuration; `site.ts` holds the one listing of the content root the other two read |
| `<site>/package.json`, `pnpm-workspace.yaml`, `tsconfig.json`, `.gitignore` | the package manifest, pnpm's install-script decisions and dependency overrides, and ignores for `node_modules/`, `build/`, `.docusaurus/` |
| `<site>/src/css/custom.css` | the stylesheet, including the version badge |
| `<content>/README.md` | the landing page, served at `/` |
| one `README.md` per content directory | an index page with `sidebar_label` and `sidebar_position` |

With no audiences the content directories are `tutorial/`, `how-to/`, `reference/`, and
`explanation/`, and the site has 5 pages. With *N* audiences each audience holds those four, and the
site has 1 + 5 × *N* pages.

If any path it would write already exists, the skill lists every conflict and writes nothing. An
existing directory with no conflicting file is written into, and the pages already in it are left
unchanged.

## What every site carries

| Property | Setting |
|---|---|
| A broken link or anchor fails the build | `onBrokenLinks: 'throw'`, `onBrokenAnchors: 'throw'` |
| `.md` is CommonMark, `.mdx` is MDX | `markdown.format: 'detect'` |
| Pages at the site root | `routeBasePath: '/'` |
| `working/` drafts are rendered by `pnpm start` only | excluded from every build, and from its navbar |
| Version badge | `DOCS_VERSION`, else `git describe --tags --match 'v[0-9]*.[0-9]*.[0-9]*'`, else none |
| Hosting | `DOCS_URL` and `DOCS_BASE_URL`, defaulting to `http://localhost:3000` and `/` |
| Pins | one exact version for every `@docusaurus/*` package, `packageManager` for pnpm, `"engines": {"node": ">=24 <25"}` |

The reason for each is a comment in the template that carries it. The skill writes no host, CI job,
edit link, or publish allowlist.

## Output

The report lists the answers with each default marked inferred, every file written, and the
verification result. That result is `verified — N of N pages built`, a failure naming each missing
route or the first build error, or `build not run` with the reason. The build is not run when Node
or `pnpm` is missing, when `pnpm` does not resolve to the pinned version, or when the user declines
the install. The skill commits nothing. `pnpm install` writes `pnpm-lock.yaml`, which the report
says to commit.

## Tool grants

**Denial set** — `WebFetch, WebSearch, Skill, NotebookEdit, Agent`

| Entry | Reason |
|---|---|
| `WebFetch`, `WebSearch` | No step fetches anything. Every template is a file in the skill's own `assets/`. |
| `Skill` | The skill invokes no other skill. |
| `NotebookEdit` | It writes no notebook. |
| `Agent` | No step fans out. |

**Pre-approval set** — `Bash(git rev-parse:*), Bash(test:*)`

| Entry | Step behind it |
|---|---|
| `Bash(git rev-parse:*)` | Step 1, resolving the repository root. |
| `Bash(test:*)` | Step 3, checking every planned path for a conflict with `test -e`; Step 5, checking every expected page with `test -f`. |

Both commands only read.

**`pnpm install` and `pnpm build` are deliberately not pre-approved.** The install reaches the npm
registry and runs in the consumer's repository, so the harness asks before each, and a declined
install is reported as a build not run.

No denied capability is used by the body.

What these declarations do **not** bound, and how their behaviour was established, is in
[Tool Grant Bounds](../../../explanation/tool-grant-bounds.md).
The skill's edit-scope section is the only control on where it writes.
