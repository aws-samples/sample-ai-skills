# Commit convention

The convention `assets/cliff.toml`'s `commit_parsers` implements, and the
block this skill records into `CLAUDE.md`/`AGENTS.md` as its final act.

## Format

```
<type>[(scope)]: <description>

[optional body]

[optional footer(s)]
```

## Parser table

| Prefix | Groups into | Bumps version | Notes |
|---|---|---|---|
| `feat:` | Added | minor | |
| `fix:` | Fixed | patch | |
| `doc:` / `docs:` | Documentation | patch | both singular and plural admitted |
| `perf:` | Performance | patch | |
| `refactor:` | Changed | patch | |
| `ci:` | CI/Build | patch | |
| `build:` | CI/Build | patch | |
| `revert:` | Reverted | patch | |
| `style:` | — | none | skipped entirely |
| `test:` | — | none | skipped entirely |
| `chore:` | — | none | skipped entirely |
| anything else (`wip`, `Add thing`, merge commits) | — | patch | matches no group; still bumps, groups into nothing |

A subject matching no parser at all still derives a patch bump but appears in
no changelog section — this is why `scripts/release.sh` refuses a release
whose generated notes carry a heading with zero entries, rather than
publishing one that describes nothing.

## Breaking changes

`feat!:` or a `BREAKING CHANGE:` footer bumps the major version pre-1.0 as a
minor-equivalent scaffolding guard (`cliff.toml`'s `breaking_always_bump_major
= false`), and ordinary major-version semantics apply at 1.0 and above. Either
way, `scripts/release.sh`'s own major-version-shape check is what actually
gates a major bump behind `CONFIRM_VERSION` — the guard that survives past the
1.0 boundary.

## Scope

Optional, parenthesized, rendered in the notes as `**scope** — `. Used to name
the domain or skill a change affects (e.g. `feat(semantic-release): ...`).
