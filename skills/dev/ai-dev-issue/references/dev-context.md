# Development Context Reference

The format of the development-context block, and the rules every skill that carries this file follows to read it, check it, fall back when it is absent, ask, and save. A skill reads only the keys its own `SKILL.md` names and follows these rules for those keys alone.

The block records facts about how a repository is developed — its forge, how the forge is reached, whether the repository is published, its spec framework, base branch, verification commands, issue tracker, and automated reviewer — so an agent session has them in context without detecting them again. A repository with no block works exactly as before: each fact is detected, and a question replaces a guess.

## The block

One block, between two markers, in the target file (see "Where the block lives"):

```markdown
<!-- ai-skills:dev-context -->
## Development context

Facts about how this repository is developed, for agents. Correct a wrong line by editing it.

- forge: gitlab
- web_host: git.example.internal
- ssh_host: ssh.git.example.internal
- project: group/project
- project_id: 1234
- cli: glab
- exposure: internal
- public_target: none
- framework: openspec
- base_branch: main
- verify: `make test`; `make lint`
- tracker: forge
- reviewer: none
- recorded: 2026-01-15
<!-- /ai-skills:dev-context -->
```

A key line is `- <key>: <value>`, one per key. Every other line between the markers — the heading, the sentence — is for people, and a reader skips it. **A key outside the table below is ignored by every reader**, so a key added later never breaks an older reader.

| Key | Value | Group |
|---|---|---|
| `forge` | `github`, `gitlab`, or another forge's lowercase name | forge |
| `web_host` | the host serving the forge's web pages and API, such as `git.example.internal` | access |
| `ssh_host` | the host `git` clones from over SSH, such as `ssh.git.example.internal`; `none` when `origin` uses HTTPS | access |
| `project` | the project's path on the forge, such as `group/subgroup/project` | access |
| `project_id` | the forge's numeric project id; `none` on a forge without one, such as GitHub | access |
| `cli` | the forge command-line tool the team uses: `gh`, `glab`, or `none` | access |
| `exposure` | `public` or `internal` — see "Exposure" | exposure |
| `public_target` | the URL a publish path pushes to, or `none` | exposure |
| `framework` | `openspec`, `spec-kit`, `kiro`, or `none` | framework |
| `base_branch` | the branch work merges into, such as `main` | base branch |
| `verify` | the commands that prove a change works, each in backticks, separated by `; ` | verification |
| `tracker` | `forge`, `none`, or a tracker and where in it, such as `jira ABC` | tracker |
| `reviewer` | the automated reviewer and where it comments, such as `review-bot (merge-request comments)`, or `none` | reviewer |
| `recorded` | the date the block was last written, `YYYY-MM-DD` | — |

A `SKILL.md` names the groups it reads. "Access" means all five access keys.

### Reserved values

- **`unresolved`** — nobody determined the fact. A reader treats it as absent.
- **`withheld`** — the fact was left out because the file holding the block is published. A reader treats it as absent and never writes the value it then derives back into that file.
- **`none`** — the fact is genuinely absent: no tracker, no reviewer, no project id.

A value taken from a default, rather than detected or answered, ends in ` (inferred)`: `- exposure: public (inferred)`. A reader uses the value without the suffix and says it was inferred.

## Where the block lives

The **target file** is the root `AGENTS.md` when it exists; otherwise the root `CLAUDE.md` when it exists; otherwise a new root `AGENTS.md`. A root `CLAUDE.md` that is only an `@AGENTS.md` import is therefore never the target when `AGENTS.md` exists. Resolve the root with `git rev-parse --show-toplevel`.

To read, look in the target file. When it holds no block, look in the other root file of the two. The block is never written to more than one file.

- **Only one marker** in a file → the fence is broken. Read no block from that file, change nothing in it, and report the broken fence with its file and line.
- **A block in each file, or two blocks in one file** → read the one in the target file, or the first, and report the duplicate. A save shows the duplicate's removal in its diff.

## Using a recorded fact

Before using a recorded fact, compare it with the live repository where the comparison is cheap:

| Fact | Live signal |
|---|---|
| `forge` | `git remote get-url origin`. The host is `github.com` → `github`. The host contains `gitlab`, or a `.gitlab-ci.yml` exists at the root → `gitlab`. Otherwise there is no live value. |
| `ssh_host` | the host of an SSH `origin` (`git@<host>:…` or `ssh://…@<host>/…`); `none` for an HTTPS `origin` |
| `web_host` | the host of an HTTPS `origin`. For an SSH `origin` there is no live value, except `github.com` and `gitlab.com`, which serve both. |
| `project` | `origin`'s path, with any leading `/` and trailing `.git` removed |
| `framework` | `openspec/` → `openspec`; `.specify/` → `spec-kit`; `.kiro/specs/` → `kiro`; none of them → `none`; more than one → no live value |
| `base_branch` | `git symbolic-ref --short refs/remotes/origin/HEAD` without its `origin/` prefix, when that ref is set |
| `exposure`, `public_target` | `.promote-target` — see "Exposure" |

- **They agree** → use the recorded value, and ask nothing about it.
- **They disagree** → use the live value. Say in one line that the recorded value is stale, naming both. Offer to update it when the run ends.
- **A stale `project`** → also ignore the recorded `project_id`: it identifies the old project.
- **A stale `ssh_host` or `web_host`** → also ignore a recorded `forge` that the live signal cannot confirm: it describes the old host. Detect the forge again.
- **No live value** (`cli`, `verify`, `tracker`, `reviewer`, and `web_host` for most SSH remotes) → use the recorded value, and state the `recorded` date when you first use it, so a reader can judge its age.

## When a fact is missing

A fact is missing when there is no block, its key is absent, or its value is `unresolved` or `withheld`. Resolve a missing fact with the skill's own detection, the steps its `SKILL.md` gives. **A missing block never stops a run.**

Ask the developer only about a fact detection cannot determine. Ask in rounds of one to four questions, each with a recommended answer, and keep asking rounds until nothing the run needs is unclear or the developer ends the interview. Two rules decide the forge and its hosts, whichever skill applies them:

- **Forge.** Apply the `forge` row of the live-signal table. When it gives no value, report the `origin` URL and ask which forge the repository uses. Do not guess one from the host's shape.
- **The web and API host is not the SSH host.** For an SSH `origin` on any host other than `github.com` and `gitlab.com`, ask for the web host rather than assuming the two are equal. When the SSH host has the form `ssh.<rest>`, recommend `<rest>`: for `git@ssh.git.example.internal:group/project.git`, recommend `git.example.internal`.

## Exposure

`exposure` is `public` when anything this repository configures publishes its content, and `internal` when nothing does. Read `.promote-target` at the root. It is parsed as `key=value` lines and never sourced or executed; blank lines, `#` comments, and lines without `=` are ignored.

- A `PUBLIC_TARGET=<url>` line → `public`, with `public_target` set to that URL.
- No `.promote-target` → no publish path is configured here. That alone does not resolve `exposure`: the project may itself be publicly visible, or published by something else. Only a found `PUBLIC_TARGET`, a forge read of the project's visibility, or the developer's answer resolves it.

**Act on the more public of the record and the live signal, whichever is newer.** `unresolved` and `withheld` count as public. A recorded `internal` beside a `.promote-target` that names a target is public. A recorded `public` with no publish configuration found is still public. A wrong `internal` publishes content that should not ship; a wrong `public` costs one confirmation.

### Whether a file is published

A file is published when any of these holds:

- a `PUBLISH_PATHS=<path>` line in `.promote-target` names the file itself or a directory above it. Each such line holds one path, and an entry may be nested, such as `docs/guides`;
- the forge reports the project itself as publicly visible;
- exposure cannot be determined, because a publish configuration exists that cannot be read in full, and the developer has not answered the exposure question.

## Saving

When a run detected or was told a fact this skill reads, and the block lacks it, records it as stale, or records it as `unresolved`, offer to save those facts at the end of the run. With no block, every fact the run resolved is one the block lacks, a detected fact included: detecting it again is the work a save spares the next run.

1. Show the change as a diff of the target file.
2. Ask one question, whose recommended answer is to save: a fact saved is a fact the next run does not ask about. Ask it with the question tool where the harness has one, before the run ends. Where it has none, ask the same question in the response and end the turn. Write only on a yes. On a decline, change no file.
3. Change only the lines for facts this run resolved in the groups this skill reads, plus `recorded`, which is today's date as `date +%F` prints it, never a date you infer. Leave every other line exactly as it is. A fact observed outside those groups was not resolved by this skill, however plainly it showed.
4. When there is no block yet, write a new one at the end of the target file, after one blank line. Build it from a block whose every line reads `unresolved`, never from the example above, then fill in only the lines this run resolved. Every key outside the groups this skill reads stays `unresolved`.
5. **Never write `exposure` or `public_target` unless this run resolved them**, as "Exposure" defines. A block saved from `origin` alone would otherwise look complete and record "not public" that nobody checked.
6. When the target file is published, write `web_host`, `ssh_host`, `project`, and `project_id` as `withheld`, and say which lines were withheld and why. `forge` and `cli` are still recorded.
7. Mark a value taken from a default with ` (inferred)`.
8. With both markers present, replace the text between them. With one, change nothing and report the broken fence.

## Headless runs

Under `--headless`, ask nothing. Take the recommended answer to every question, and mark each answer taken that way as inferred in the run's own output. **Offer no save and write no block**: a save writes into a file a person wrote, and the confirmation stands in for that person. Where the run would have shown a diff, print it instead. The recommended answer for exposure is `public`.

When the forge is unknown and the run needs it, stop and name the forge as the unresolved fact. Picking a forge would send every later request to a host nobody chose.
