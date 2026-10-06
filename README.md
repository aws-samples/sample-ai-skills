# ai-skills

Reusable skills for AI coding agents. They give an agent your project's patterns, constraints, and
conventions, so its output is consistent from one run to the next.

Each skill is a self-contained directory holding a `SKILL.md` and the reference material it needs,
following the [Agent Skills](https://agentskills.io) format, so any coding agent that loads skills
can use them.
Skills are grouped by domain under [`skills/`](skills/). Domains are independent, so you can install
one skill without the others.

| Domain | Purpose | # Skills |
|---|---|---|
| [**adr**](docs/skills/adr/README.md) | a project's architecture decision log | 1 |
| [**agents**](docs/skills/agents/README.md) | the files a coding agent reads: agent-context files and new skills | 3 |
| [**dev**](docs/skills/dev/README.md) | recording how a repository is developed, filing issues, carrying a spec or issue to a merge-ready pull or merge request, and the forge's issue, request, and review templates | 4 |
| [**human-docs**](docs/skills/human-docs/README.md) | prose documents written for people, and their export to PDF, Word, and Excel | 5 |
| [**release**](docs/skills/release/README.md) | versioning and release notes derived from Conventional Commits, and an optional public publish path | 1 |
| [**research**](docs/skills/research/README.md) | the spec-driven development loop: a working folder, research, a plan, implementation, and retirement | 5 |
| [**software-docs**](docs/skills/software-docs/README.md) | a project's documentation tree and the site that builds it | 2 |

## Install

### Manual

Each skill is one directory under `skills/<domain>/` in this repository, holding a `SKILL.md` and
usually a `references/` folder. Copy the whole skill directory, `references/` included, into the
skills directory your agent reads. Use the project-level directory to install for one project, or
the user-level directory to make the skill available in every project. For Claude Code those are
`.claude/skills/` and `~/.claude/skills/`:

```sh
cp -R skills/research/ai-plan ~/.claude/skills/
```

For any other agent, see its documentation for where its skills directory is.

### Installer

The installer copies the skills you choose into the skills directory of each agent you choose:
Claude Code, Kiro, Codex, OpenCode, pi, or Cursor. It runs with [`uv`](https://docs.astral.sh/uv/),
and shows every file it will write before it writes anything.

```sh
uvx --from git+https://github.com/aws-samples/sample-ai-skills@vX.Y.Z ai-skills
```

![The installer's first screen, choosing which agents to install for](docs/how-to/images/installer-1.png)

[Install Skills with the Installer](docs/how-to/install-skills-with-the-installer.md) walks
through every screen, the flags for a non-interactive install, and what each agent receives.

## Documentation

Start at [`docs/README.md`](docs/README.md). It covers what each skill does, how to invoke it, task
guides, and the reasoning behind the conventions.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
