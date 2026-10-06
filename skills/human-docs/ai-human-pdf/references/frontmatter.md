# Frontmatter and supported markdown

What `scripts/render_pdf_cli.py` reads from a document. Read by the skill only when a user asks what
is supported, or when a renderer error names a frontmatter key.

## Frontmatter

The frontmatter is a YAML block between a `---` line that opens the file and the next `---` line.
Every key is optional, and these are the only keys the renderer reads. Any other key is ignored.

```yaml
---
title: Q3 Platform Review
subtitle: Prepared for the steering group
organization: Example Corp
client: Acme
classification: Internal
industry: Logistics
date: 2026-10-01
accent: "#0B5FFF"
logo: ./brand/logo.png
---
```

| Key | Where it appears | When unset |
|---|---|---|
| `title` | the cover, the running footer, and the PDF's title metadata | the body's single H1; else the file name without `.md`, which the skill offers as the default when it asks |
| `subtitle` | the cover, under the title | left out |
| `organization` | the cover and the running header, as `organization × client`, and the PDF's author metadata | left out, with no separator |
| `client` | the same line | left out, with no separator |
| `classification` | the cover's footer and the running footer, after the title | left out, with no separator |
| `industry` | nowhere: the layout draws no industry field, so the key has no effect | — |
| `date` | the cover's `Exported:` line | the day of the run |
| `accent` | every accent-coloured element: the rule under each H1, the cover's stripes, its `organization × client` line and the rule under it, the subtitle, `###!` headings, the header and footer rules, and the bar of a `[!WARNING]` admonition | `#2F5D8A` |
| `logo` | the cover, under the title, at most 200 points wide | no logo |

Each key's flag overrides it: `--title`, `--subtitle`, `--organization`, `--client`,
`--classification`, `--industry`, `--date`, `--accent`, and `--logo`. The skill passes a flag only
for a value the user stated in the request.

**`accent`** must be six hex digits after a `#`, written `#RRGGBB`. Quote it: YAML reads an unquoted
`#` as the start of a comment, so `accent: #0B5FFF` is an empty value. A value that is not `#RRGGBB`
stops the run with the value and its source named, and nothing is written.

**`logo`** is a path to an image file, resolved against the markdown file's directory when it is
relative. A path that names no file, or a file the renderer cannot read as an image, stops the run
with the path and its source named, and nothing is written.

No other visual property can be set: the fonts are the PDF built-ins Helvetica and Courier, and the
page size is US Letter.

## Supported markdown

| Feature | Syntax |
|---|---|
| Headings, H1 to H3 | `#`, `##`, `###`. With exactly one H1 and no `title:`, the H1 becomes the cover title and every other heading moves up one level. |
| An H3 in the accent colour | `###! Heading` |
| Bold, italic, inline code | `**b**`, `*i*`, `` `code` `` |
| Bullet lists, two levels | `- item`, and an indented `- item` beneath it |
| Tables | `\| h1 \| h2 \|` |
| Column widths for the next table | `<!-- widths: 30% 70% -->`, also `pt` or bare points |
| Code blocks | a fenced block, with or without a language |
| Mermaid diagrams | a fenced `mermaid` block. Drawn as an image through a pinned `@mermaid-js/mermaid-cli`, fetched by `npx` on first use, when `node` and `npx` are on `PATH`. Otherwise drawn as a code block, and the run prints a note. |
| Width of the next Mermaid diagram | `<!-- mermaid-width: 300 -->`, in points |
| Admonitions | `> [!INFO]`, `> [!WARNING]`, `> [!CRITICAL]` |
| Page breaks | `\pagebreak` on its own line, or `<!-- pagebreak -->` |
| Horizontal rules | `---` |
| Table of contents | generated from the H1s. `--toc-depth 2` or `3` adds H2s or H3s, and `--no-toc` leaves it out. |

An image written in markdown, `![alt](path)`, is not drawn: the renderer prints a warning naming it
and leaves it out.
