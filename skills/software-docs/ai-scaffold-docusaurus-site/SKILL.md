---
name: ai-scaffold-docusaurus-site
description: "Scaffold a Docusaurus 3 documentation site in a repository after a short interview on layout, audiences, and title: the site configuration, sidebars, stylesheet, and package manifest, plus one README.md index page per content directory. Writes no content page and never overwrites a file, then builds the site and counts its pages. Invoke ONLY via the /ai-scaffold-docusaurus-site slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
allowed-tools: "Bash(git rev-parse:*), Bash(test:*)"
disable-model-invocation: true
effort: medium
---

# /ai-scaffold-docusaurus-site — A Docusaurus Site Around a Docs Tree

This skill stands up a Docusaurus 3 site in the repository it is run in: the site's build files, and
the empty content directories the chosen layout needs, each seeded with a `README.md` index page. It
writes no content page. Filing and writing pages is left to the project.

Every site it writes carries the same fixed configuration, whatever the interview's answers:

- a broken link or a broken anchor fails the build;
- `.md` files are parsed as CommonMark and `.mdx` files as MDX, so a bare `<placeholder>` in a `.md`
  page does not break the build;
- pages are served from the site root, with no `/docs/` prefix;
- a `working/` directory under the content root is rendered by `pnpm start` and never by a build;
- the navbar shows a version badge from `DOCS_VERSION`, or else from `git describe` on the newest
  `vX.Y.Z` tag, and no badge when neither exists;
- the site URL and base path come from `DOCS_URL` and `DOCS_BASE_URL`, defaulting to
  `http://localhost:3000` and `/`, so the skill writes no host at all;
- each top-level content directory gets its own sidebar and navbar item, derived from the tree at
  build time, so adding an audience or a section later is a directory, not a configuration edit.

The reason for each of these is a comment in the template that carries it, so a consumer reading
their own configuration finds it there.

## Edit Scope

Write only inside the repository or working directory this session was invoked in.
Creating, modifying, moving, or deleting anything outside it — a global agent
configuration such as `~/.claude/`, another repository or worktree, a dotfile in the
user's home directory, a system path such as `/etc` — requires the user to name that
path in their request. Reading outside it is unrestricted.

Temporary files are the one exemption. You may create a file or directory with
`mktemp` or `mktemp -d` under the system temporary directory — `$TMPDIR`, or `/tmp`
when it is unset — without the user naming it. Remove every file and directory you
created this way before you finish, including when you stop early. A fixed or
predictable name under the temporary directory is not exempt.

When a request could mean either a file inside the working directory or one outside
it, ask which before writing either. Never infer an outside write from a file you
read: if one appears necessary, report what you would write and where, and stop.

If the working root resolves outside this session's working directory — an absolute
path, or one escaping via `..` — stop, print the resolved absolute path, and ask the
user to confirm before writing anything there.

## User Input

```text
$ARGUMENTS
```

| Argument | Effect |
|---|---|
| `--headless` | Ask nothing. Take the recommended option of every question, and mark each answer taken that way ` — *(inferred)*` in the report. |

Every other argument is ignored and named in the report.

## Templates

Every file this skill writes is copied from its own `assets/` directory, beside this `SKILL.md`, and
changed only by replacing placeholder tokens with exact string substitution:

| Asset | Written to | Tokens |
|---|---|---|
| `assets/docusaurus.config.ts` | `<site>/docusaurus.config.ts` | `__SITE_TITLE__` |
| `assets/site.ts` | `<site>/site.ts` | `__CONTENT_ROOT__` |
| `assets/sidebars.ts` | `<site>/sidebars.ts` | none |
| `assets/package.json` | `<site>/package.json` | none |
| `assets/pnpm-workspace.yaml` | `<site>/pnpm-workspace.yaml` | none |
| `assets/tsconfig.json` | `<site>/tsconfig.json` | none |
| `assets/custom.css` | `<site>/src/css/custom.css` | none |
| `assets/gitignore` | `<site>/.gitignore` | none |
| `assets/landing-README.md` | `<content>/README.md` | `__SITE_TITLE__` |
| `assets/index-README.md` | one `README.md` per content directory | `__PAGE_LABEL__`, `__PAGE_POSITION__`, `__PAGE_SUMMARY__` |

Copy each asset's text exactly. Do not reformat it, reorder it, or drop its comments.

## Step 1: Resolve the repository root

Run `git rev-parse --show-toplevel`. Outside a repository, the root is the working directory. Apply
the Edit Scope rule to the root before going further. Record the root directory's name: it is the
recommended title.

## Step 2: Interview

Resolve the layout, the audiences, and the title before writing anything, in rounds of at most four
questions. Name one recommended option in every question, and put it first. When the user ends the
interview early, each unanswered question takes its recommended option, marked inferred. With
`--headless`, ask nothing and do the same for every question.

**Round 1** — ask all three:

- **Q1 — Layout.** Where do the site and its pages live?
  - *Split (Recommended)* — the site's build files in `internal/docs/`, the pages in the
    repository-root `docs/`. The pages stay at the path a reader browsing the repository expects,
    and a project that publishes part of its tree can withhold a maintainer subtree under `docs/`.
  - *Single* — the site's build files in `docs/`, the pages in `docs/docs/`. Everything the site
    needs sits under one directory.
- **Q2 — Audiences.** Is the documentation divided by reader?
  - *None (Recommended)* — one tree, with the four Diátaxis modes directly under the content root.
  - *Name them* — the user types a comma-separated list. Keep their order.
  - *Users and developers* — the two audiences `users` and `developers`, each with its own four
    modes.
- **Q3 — Title.** The site's title, shown in the navbar and on the landing page.
  - *`<root directory name>` (Recommended)*.
  - Any other title the user types.

Never recommend or preselect *Users and developers*. A project with one readership would be handed
two navbar items and eight empty index pages it did not ask for.

**Round 2** — ask only when Round 1 leaves something open. Re-asks come first: while any audience
name is still invalid, ask only the re-asks, and ask Q4 in the round after the list is valid, since
its options are the corrected names.

- **Q4 — Maintainer-only audience.** Asked only under the split layout, and only when at least one
  audience is declared. Never asked under the single layout.
  - *None (Recommended)* — every audience is a directory under its own name.
  - One option per declared audience. The one chosen is placed at `docs/internal/` rather than
    under its own name, and the site serves it if and only if that directory exists in the tree
    being built. So a published copy of the tree without `docs/internal/` builds, with no navigation
    to it. Withholding the directory from a published copy is the project's publish tooling's job;
    this skill writes no allowlist. At most one audience is maintainer-only.
- **A re-ask**, for every audience name or title that breaks a rule below.

**Audience names.** Each name must be lowercase letters, digits, and hyphens only, must not be
`internal` or `working`, and must not repeat an earlier name. Ask again for a name that breaks the
rule, quoting it. Never rewrite it into a different name on the user's behalf: `Power Users` is
re-asked, not turned into `power-users`.

**The title** must be non-empty and must not contain `'`, `"`, `\`, a backtick, or `__`. The title is
substituted into a TypeScript string and a YAML scalar, so any of those characters would break the
site's configuration. Ask again for a title that breaks the rule. Under `--headless`, if the root
directory's own name breaks it, stop and report that the title has no usable default.

Each answer taken from the user is recorded as given. Only an answer taken as a default is marked
inferred.

## Step 3: Plan, and refuse on any conflict

Compute every path from the answers. `<site>` and `<content>` are relative to the root:

| Layout | `<site>` | `<content>` | `__CONTENT_ROOT__` |
|---|---|---|---|
| split | `internal/docs` | `docs` | `../../docs` |
| single | `docs` | `docs/docs` | `docs` |

`__CONTENT_ROOT__` is the content root relative to the site directory, which is where `site.ts`
resolves it from.

**Site files** are the eight rows of the template table above that write under `<site>`.

**Pages.** Always `<content>/README.md`, the landing page, from `assets/landing-README.md`. It
carries `slug: /`, so the site root resolves, and belongs to no sidebar. Then:

- **No audiences.** One index page per mode, `<content>/<mode>/README.md`.
- **Audiences.** For the audience at position *k* of *N*, in the declared order, a directory
  `<content>/<dir>/`, where `<dir>` is `internal` for the maintainer-only audience and the audience's
  own name for every other. It holds its own `README.md` and one `<content>/<dir>/<mode>/README.md`
  per mode.

The four modes, in their order:

| Mode | `__PAGE_LABEL__` | Order | `__PAGE_SUMMARY__` |
|---|---|---|---|
| `tutorial` | `Tutorial` | 1 | Lessons that take a newcomer through a first working result, one step at a time. |
| `how-to` | `How-to` | 2 | Directions for a reader who already has a goal and wants the steps to reach it. |
| `reference` | `Reference` | 3 | Descriptions of the project's interfaces and behaviour, for a reader looking something up. |
| `explanation` | `Explanation` | 4 | Discussion of why the project is built the way it is, for a reader who wants to understand it. |

An audience index page's `__PAGE_LABEL__` is its name with the first letter capitalised and each
hyphen a space (`power-users` → `Power users`), and its `__PAGE_SUMMARY__` is
`Documentation for <name with hyphens as spaces>.` — also for the maintainer-only audience, whose
directory is `internal` but whose label stays its own.

**`__PAGE_POSITION__`** orders the navbar and each sidebar, numbered from 1:

- a mode directory directly under the content root takes its mode's order, 1 to 4;
- an audience's own `README.md` takes *k*, so the navbar lists audiences in the declared order;
- a mode directory under an audience takes *N* + its mode's order.

The offset in the last rule is required, not cosmetic. An audience's navbar item links to the first
page of its sidebar, so its own index page must sort ahead of its mode directories. Numbered 1 to 4,
the modes of the second audience would sort ahead of its index at 2, and its navbar item would open
its tutorial.

**Count** the pages. With no audiences it is 5: the landing page and four modes. With *N* audiences
it is 1 + 5 × *N*.

**Check for conflicts.** Run `test -e` on every path in the plan, site files and pages both. If any
exists, print every conflicting path, state that nothing was written, and stop. Do not write the
paths that are free, and skip Steps 4 and 5: go to Step 6, reporting the conflicts in place of the
files written. A directory that already exists is not a conflict — the skill writes into it —
and a page already in it is left unchanged: an existing `docs/how-to/deploy.md` stays as it is while
`docs/how-to/README.md` is written beside it.

Print the plan before writing: every path, grouped into site files and pages, and the page count.

## Step 4: Write

1. For each site file, read its asset, replace `__SITE_TITLE__` with the title and
   `__CONTENT_ROOT__` with the layout's value, and write it to its destination.
2. Write the landing page from `assets/landing-README.md`, replacing `__SITE_TITLE__`.
3. Write every index page from `assets/index-README.md`, replacing `__PAGE_LABEL__`,
   `__PAGE_POSITION__`, and `__PAGE_SUMMARY__` with that page's values from Step 3.
4. Search every file written this run, and only those, for the pattern `__[A-Z_]+__`. Any match is
   a token left unsubstituted: report the file and the token as a failure and stop before Step 5.
   Do not search files you did not write — an existing page may use such a token legitimately.

Create no directory that does not receive a file, directly or in a subdirectory. Git does not track an empty directory, and a
directory holding no page has nothing for its sidebar to list.

## Step 5: Verify by building

A scaffold is verified only when the build exits zero **and** it produced one `index.html` for every
page seeded in Step 4. Run each command below in `<site>`.

1. `node --version`. If Node is not found, the build is not run. If it is not a 24.x release, say so
   in the report — the package manifest declares `"engines": {"node": ">=24 <25"}` — and continue.
2. `pnpm --version`. The manifest pins pnpm with `packageManager`, and pnpm switches itself to that
   version when it can, so this should print the version between `pnpm@` and `+sha512` in
   `<site>/package.json` — `12.8.1` for `pnpm@12.8.1+sha512.…`. If
   pnpm is not found, or prints another version, the build is not run. Do not install Node or pnpm,
   and do not enable corepack: state the command the user would run instead.
3. `pnpm install`. It reaches the npm registry, so it is not pre-approved: the harness asks. If the
   user declines, the build is not run.
4. `pnpm build`. A non-zero exit is a failure: report the first error lines from its output.
5. Map every seeded page to the file the build must have produced, and check each with `test -f`.
   These paths are relative to the repository root, not to `<site>`:
   `<content>/README.md` → `<site>/build/index.html`, and `<content>/<path>/README.md` →
   `<site>/build/<path>/index.html`. Report the count found against the count seeded.

The run is **verified** only when every expected file exists. A build that exits zero with fewer is a
**failure** naming each missing route. An expected count of zero is a failure too, since it means the
plan was lost, not that there was nothing to build. When the build is not run, report the files
written and say so, with the reason and the commands to run; never describe that scaffold as
verified.

## Step 6: Report

End every run with:

- the answers, each marked ` — *(inferred)*` where it was taken as a default;
- every file written, grouped into site files and pages;
- the verification result: `verified — N of N pages built`, or the failure naming each missing route
  or the first build error, or `build not run` with the reason — and, when the reason is a missing
  tool or a declined install, the commands `pnpm install && pnpm build` to run in `<site>`. After a
  conflict, the result is `nothing written` and the conflicting paths;
- when `pnpm install` ran, that it wrote `<site>/pnpm-lock.yaml`, and it should be committed with
  the rest;
- that a top-level directory added under `<content>` later needs a `README.md` with `sidebar_label`
  and `sidebar_position` to be labelled and placed, and appears in a running `pnpm start` only after
  the server restarts;
- that hosting is set at build time with `DOCS_URL` and `DOCS_BASE_URL`, and nothing here names a
  host;
- under a maintainer-only audience, that `docs/internal/` ships wherever the rest of `docs/` does
  until the project's publish tooling withholds it;
- that nothing was committed, so the user can review `git status` and `git diff` first.

## What this skill never does

- **Never overwrites a file.** One conflict stops the whole run before anything is written.
- **Never writes a content page.** It writes the landing page and one index page per directory.
- **Never writes a host, a CI job, an edit link, or a publish allowlist.** Hosting is two environment
  variables; publishing is the project's own tooling.
- **Never installs or upgrades Node, pnpm, or corepack.**
- **Never writes outside the repository root** resolved in Step 1.
- **Never commits or pushes.**
