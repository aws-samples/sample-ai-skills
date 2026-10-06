---
title: "human-docs"
sidebar_label: "human-docs"
sidebar_position: 5
---

# `human-docs`

Skills for prose documents written for people, and for exporting them. Five ship; each is invoked
only by its slash command.

| Skill | What it does |
|---|---|
| [`ai-human-docx`](./ai-human-docx/) | exports one markdown file to a Microsoft Word document beside it, optionally styled by a `.dotx` template, with a bundled converter that needs only `uv` |
| [`ai-human-draft`](./ai-human-draft/) | turns a document folder into the delivered document, following the outline's guidance for each section, and on a later run revises that draft section by section, keeping the user's edits |
| [`ai-human-outline`](./ai-human-outline/) | turns a document folder into a heading hierarchy, with drafting guidance under every heading and a table mapping each objective to a section, and creates the folder when none matches |
| [`ai-human-pdf`](./ai-human-pdf/) | exports one markdown file to a PDF beside it, with a cover page, a table of contents, and Mermaid diagrams, in a neutral palette with an optional accent colour and cover logo |
| [`ai-human-xlsx`](./ai-human-xlsx/) | exports a markdown file or a working folder to one Excel workbook, with tables as typed sheets, prose as rows, hyperlinks, and embedded images, after confirming the mapping |
