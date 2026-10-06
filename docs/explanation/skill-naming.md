---
title: "Skill Naming"
sidebar_label: "Skill Naming"
sidebar_position: 2
---

# Skill naming

A skill's name tells a consumer two things before they open it: how often the skill is run, and
whether running it changes their repository. Three rules produce that, and a fourth governs the one
directory in a domain that is not a skill.

## Every name begins with `ai-`

Every skill in this collection is named `ai-<rest>`. A skill's name is three things at once — its
directory name under `skills/<domain>/`, the `name:` value in its `SKILL.md` frontmatter, and its slash
command — and the three are the same string. `skills/research/ai-plan/` declares `name: ai-plan` and is
invoked as `/ai-plan`.

The prefix groups this collection's skills together wherever a consumer lists them beside skills from
other sources: typing `/ai-` offers every one of them and nothing else.

## A run-once skill that changes the repository is named `ai-scaffold-*`

A skill that is normally run **once per repository**, and whose run writes configuration, scripts, CI
jobs, or agent-context files into that repository, is named `ai-scaffold-<rest>`, whichever domain it
belongs to. A skill run on each piece of work does not carry the `scaffold` token.

The reason is completion. The commands typed every day should be the shortest to reach, and a setup
command sharing their prefix gets in the way of them. Typing `/ai-d` offers `ai-dev-issue`, not the
skill that generated the repository's issue templates, because that skill's name begins
`ai-scaffold-`.

The shipped skills that configure a repository once are:

| Skill | What it writes |
|---|---|
| [`ai-scaffold-agents-md`](../skills/agents/ai-scaffold-agents-md/) | a `CLAUDE.md` pointer beside every `AGENTS.md`, and a convention block in the root `AGENTS.md` |
| [`ai-scaffold-dev-templates`](../skills/dev/ai-scaffold-dev-templates/) | issue templates, a pull or merge request template, and review rules, where the forge reads each one |
| [`ai-scaffold-release`](../skills/release/ai-scaffold-release/) | a `git-cliff` configuration, a release script, a forge-release script, and CI jobs |

Every other shipped skill — researching, planning, implementing, filing an issue, writing a decision
record — is run repeatedly, and none of their names contains `scaffold`.

## A domain token appears only when the name needs it

A name includes its domain's token only when the name without it would be too generic to identify the
skill among skills from other collections.

| Name | Domain token | Why |
|---|---|---|
| `ai-plan` | none | the action is unambiguous on its own |
| `ai-make-skill` | none | the same |
| `ai-agent-context` | `agent` | `ai-context` would say nothing about which context |
| `ai-human-draft` | `human` | `ai-draft` would say nothing about what is drafted |

The rest of a name names the action or the artifact the skill produces. It does not carry a word
describing the status of that artifact, such as `recommended`: a planned skill that writes a
repository's development context is `ai-scaffold-dev-context`, not `ai-dev-recommended-context`.

## A domain's reference source is hidden and named for its domain

Some reference files are shared by several skills in a domain. Each skill carries its own copy in its
`references/` directory, so that a skill installed alone still has every file it reads. The source
those copies are checked against lives once per domain, in a directory named
`.ai-<domain>-reference/` directly under `skills/<domain>/`:

```text
skills/research/
├── .ai-research-reference/   # the source; holds no SKILL.md
├── ai-plan/
│   ├── SKILL.md
│   └── references/           # the copy ai-plan reads
└── …
```

Today `research` and `adr` have one. A domain with no shared file has none.

Two properties of that name each do one job.

**The leading dot keeps the source out of the most likely hand-install.** A shell glob does not match
a hidden entry, so copying a domain's skills by glob copies every skill with its own `references/`
directory and leaves the source behind. Other copy methods include it:

| Command | Copies `.ai-research-reference/` |
|---|---|
| `cp -r skills/research/* <dest>/` | no — `*` does not match a name beginning with `.` |
| `cp -r skills/research <dest>/` | yes — the directory is copied whole |
| `rsync -a skills/research/ <dest>/` | yes |
| `tar -cf - -C skills research \| tar -xf - -C <dest>` | yes |

A shell with `dotglob` set (bash) makes `*` match hidden names too, so the first row holds only for a
shell's default settings.

**The domain prefix stops two domains' sources merging.** If the source is copied anyway, it keeps its
domain in its name. `research` and `adr` both hold a `manifest-update.md` and a `voice.md`. The two
pairs are identical today, but each domain maintains its own. Copying both domains into one destination
leaves two directories, `.ai-research-reference/` and `.ai-adr-reference/`, rather than one shared
directory in which the second domain's files overwrite the first's once the two pairs differ.

Neither property prevents every copy, and neither needs to. A copied source holds no `SKILL.md`, so a
harness that discovers skills by that file loads nothing from it. The cost of copying one is a stray
directory, not a broken or duplicated skill.
