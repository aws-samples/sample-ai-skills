# Audience Directories

How a docs tree partitioned by reader is recognised, how a request selects one of its partitions, and where the page then goes. Read this file when the audience set is non-empty, or when the request carries one of the four positional phrases below.

**Not Diátaxis doctrine.** Diátaxis supplies one axis, the four modes. This collection adds a second, **audience**, that a project may partition its docs tree by, with the four modes inside each partition. A project with no audience directories has one readership, and every rule here then selects nothing.

## 1. The directories are the declaration

An **audience directory** is a directory directly under the docs root that is not a mode directory (`tutorial`, `how-to`, `reference`, `explanation`), is not the working root, and itself holds at least one mode directory. The **audience set** is the names of the audience directories. `docs/users/how-to/` and `docs/developers/how-to/` make the set `users` and `developers`.

Nothing else declares an audience:

- **No configuration key.** An audience is never read from `.ai-skills.toml` or any other file. An `audiences = ["users"]` line there is an unrecognized key — warn and ignore it, per the project-context reference — and with no `docs/users/` directory the set is empty.
- **No inference from wording.** A request never adds a name to the set, whatever it says.
- **No audience directory is ever created by this skill.** A person creates one, by hand or with a site scaffold. A directory is also what a generated site derives a sidebar and a navigation item from, so it is what makes an audience reachable; a directory this skill invented would be a partition no one chose.

**An example is not a default.** `users` and `developers` appear in this file as examples. Never offer either name, recommend it, or treat a project as having it unless its directory exists.

## 2. Selecting an audience — by position only

A name selects an audience only in one of four positions in the request, where `<name>` is the single word — letters, digits, and hyphens — standing in that position:

- `for the <name>` — "for the developers, document how to cut a release"
- `<name>-facing` — "a users-facing page on export formats"
- `in <name> docs` — "in developers docs, describe the build cache"
- a leading `<name> docs:` — "users docs: how to reset a password"

A word anywhere else is **content, not a selector.** "explain how the cache serves the user" names no audience, because `user` is the object of "serves", not in a selecting position.

Match `<name>` **exactly** against the set, ignoring letter case only. **Never resolve a near-miss to the closest name**: "for the devs" does not select `developers`. A near-miss resolved silently is the one failure here with no detection at all — the run reports a confident resolution and the page lands under the wrong reader.

The rules below are mechanical: a count, a directory name, and a phrase position, never a judgment about who a page "feels like it is for."

| Audience set | Request | Result |
|---|---|---|
| empty | no positional phrase | no audience; print nothing about audiences except the report line |
| empty | a positional phrase | no audience; place the page at the mode root and print one line: no audience directory exists under the docs root, so the phrase selected nothing. Ask nothing, and create no directory |
| one member | no positional phrase | that member |
| non-empty | one or more phrases, all matching the same one name | that name |
| two or more members | no positional phrase | **ask** |
| non-empty | a phrase matching no name | **ask** |
| non-empty | phrases matching two different names | **ask** |

The split between the first two rows and the last three is the point: **ask when the answer exists and is ambiguous; report when it does not exist.** With an empty set there is no name to offer, so a question would have no valid option.

A spurious positional match — "for the first time" in a tree with audiences — asks, and the answer settles it. That costs one question and never files a page under the wrong reader.

## 3. Asking which audience

Offer every name in the set as an option, and no other. Describe each option with the first non-blank line after the H1 of that audience directory's index page — a site scaffold writes `Documentation for <name>.` there — or with nothing when it has no index page. Recommend no option: a recommended default is a guessed reader.

Write nothing until the answer names exactly one audience in the set. On a harness with no question tool, ask the same question in the response, end the turn, and write nothing.

## 4. The two placements

| Selected | The page is written to |
|---|---|
| an audience | `<docs_root>/<audience>/<mode>/<slug>.md` |
| no audience | `<docs_root>/<mode>/<slug>.md` |

There is no third placement:

- **Never below the modes**, at `<docs_root>/<mode>/<audience>/`. A mode's subdirectory is far more often a topic than a reader — reference is supposed to mirror the product in subdirectories — so reading one as an audience invents a partition nobody declared.
- **Never beside the modes**, at `<docs_root>/<audience>/<slug>.md`. A page directly in an audience directory has no mode, which abandons the one-mode-per-page discipline. SURVEY and ASSESS report such an existing page as unfiled.

## 5. One path, one write, one report

Compute the path once. The write and the report both use that one value, and the report prints the resolved audience beside it:

```text
audience: developers (from "for the developers") → docs/developers/how-to/how-to-cut-a-release.md
audience: users (the only audience) → docs/users/reference/export-formats.md
audience: users (answered) → docs/users/how-to/how-to-reset-a-password.md
audience: none → docs/how-to/how-to-configure-the-cache.md
```

**This line is the only check the audience axis has.** A page filed under the wrong reader renders correctly, links correctly, and passes a site build, so nothing downstream fails on it. Printing the path beside the audience makes the claim checkable against the filesystem. When the resolution is wrong, the user re-runs with an explicit `for the <name>` phrase; this skill reports and never offers to move a page it has just written.
