---
title: "dev"
sidebar_label: "dev"
sidebar_position: 4
---

# `dev`

Skills for the development loop around a forge — the service hosting a repository, its issues, and
its pull or merge requests, such as GitHub or GitLab. Each is invoked only by its slash command.

| Skill | What it does |
|---|---|
| [`ai-dev-autopr`](./ai-dev-autopr/) | carries a spec, issue, or ticket through implementation, verification, and automated review to a merge-ready PR/MR, and stops before merging |
| [`ai-dev-issue`](./ai-dev-issue/) | investigates a problem, then files one issue in the project's tracker, or a dated markdown file when there is none |
| [`ai-scaffold-dev-context`](./ai-scaffold-dev-context/) | records which forge a repository uses and how it is reached, whether it is published, its spec framework, base branch, verification commands, tracker, and automated reviewer, as one block in the root agent-context file |
| [`ai-scaffold-dev-templates`](./ai-scaffold-dev-templates/) | writes the bug report and enhancement issue templates, the pull or merge request template, and the review rules where the repository's forge reads each one |
