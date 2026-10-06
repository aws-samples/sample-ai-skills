---
title: "agents"
sidebar_label: "agents"
sidebar_position: 3
---

# `agents`

Skills for the files a coding agent reads. Three ship: one writes the context files for a source
directory, one arranges them so that every coding agent reads the same text, and one writes a new
skill. Each is invoked only by its slash command.

| Skill | What it does |
|---|---|
| [`ai-agent-context`](./ai-agent-context/) | writes a `CLAUDE.md` of mistake-preventing facts and a `README.md` reference for one source directory, after reading every file in it |
| [`ai-make-skill`](./ai-make-skill/) | writes a new skill from a description, as a vendor-neutral Agent Skills folder, adding agent-specific keys only for an agent the user confirms |
| [`ai-scaffold-agents-md`](./ai-scaffold-agents-md/) | makes `AGENTS.md` the single source of agent context, writes a `CLAUDE.md` pointer beside each one that only imports it, and moves content out of an existing `CLAUDE.md` after confirmation |
