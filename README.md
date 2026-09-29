# ai-skills

Reusable skills for AI coding agents. They give an agent your project's patterns, constraints, and
conventions, so its output is consistent from one run to the next.

Each skill is a self-contained directory holding a `SKILL.md` and the reference material it needs,
following the [Agent Skills](https://agentskills.io) format, so any coding agent that loads skills
can use them.
Skills are grouped by domain under [`skills/`](skills/): one domain covers a spec-driven development
workflow, taking a feature from research through planning to implementation; another sets up
versioning and release notes derived from Conventional Commits. Domains are independent, so you can
install one skill without the others.

## Install a skill

Copy a skill's directory, including its `references/` folder, into the skills directory your agent
reads, either at the project level or at the user level to make it available in every project. See
your agent's documentation for where that directory is.

## Documentation

Start at [`docs/README.md`](docs/README.md). It covers what each skill does, how to invoke it, task
guides, and the reasoning behind the conventions.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
