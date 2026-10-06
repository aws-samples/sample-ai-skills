---
title: "adr"
sidebar_label: "adr"
sidebar_position: 2
---

# `adr`

One skill that keeps a project's architecture decision log: a directory of dated records, one per
decision, each carrying a status. It is invoked only by its slash command.

| Skill | What it does |
|---|---|
| [`ai-adr`](./ai-adr/) | stands the log up on first run, then writes records and moves them through propose, accept, and decline |

The canonical shared references for this domain live at `skills/adr/.ai-adr-reference/`
(`adr-format.md`, `framework-detection.md`, `manifest-update.md`, `voice.md`). The skill carries its
own copy of the references it cites, in its `references/` folder.
[Skill Naming](../../explanation/skill-naming.md) explains why the source directory's name starts
with a dot.
