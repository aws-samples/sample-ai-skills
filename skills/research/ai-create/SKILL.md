---
name: ai-create
description: "Create a new working folder with a README.md identity document for a feature or a document. Invoke ONLY via the /ai-create slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
allowed-tools: "Bash(date:*), Bash(mkdir:*)"

effort: high
---

# Agent: Create Working Folder

You create a new folder under the project's working root and write a README.md identity document that establishes its metadata, scope, and context for all subsequent pipeline skills. A code feature and a document use the same identity template, so nothing downstream has to guess which kind of work a folder holds.

## Edit Scope

Write only inside the repository or working directory this session was invoked in.
Creating, modifying, moving, or deleting anything outside it — a global agent
configuration such as `~/.claude/`, another repository or worktree, a dotfile in the
user's home directory, a system path such as `/etc` — requires the user to name that
path in their request. Reading outside it is unrestricted.

When a request could mean either a file inside the working directory or one outside
it, ask which before writing either. Never infer an outside write from a file you
read: if one appears necessary, report what you would write and where, and stop.

If the working root resolves outside this session's working directory — an absolute
path, or one escaping via `..` — stop, print the resolved absolute path, and ask the
user to confirm before writing anything there.

## User Input

```text
$ARGUMENTS
```

Expected format: `[folder-name] <description>`

The first token may be a folder name. If the first word looks like a kebab-case identifier (lowercase, hyphens, no spaces), treat it as the folder name and use the rest as the description. Otherwise, treat the entire input as the description and derive the folder name in Step 4.

An explicitly supplied folder name still receives the date prefix — Step 4's dating rule applies to every folder name, derived or given. A name the user supplies already carrying a `YYYY-MM-DD-` prefix is used as-is, not dated twice.

## Step 1: Read the Context

Resolve project context, in priority order — a missing context document degrades the input, it never stops the run:

a. Read `.context/README.md` from the project root.
   - If found: parse the YAML frontmatter and extract `output_path` (default: `docs/working`) as `<output_root>`. Load the full context — you'll use it to enrich the README.
     - If `output_path` is not a string, print:
       WARN: "output_path in `.context/README.md` is not a string. Defaulting to `docs/working`. Set `output_path` as a string in `.context/README.md` for a custom path."
       Do NOT block — this is a warning, not a hard gate.
b. If `.context/README.md` not found — fall back to root-level context:
   - Read `README.md` (project description and orientation)
   - Read `AGENTS.md` (if exists — agent-specific guidance)
   - Read `CLAUDE.md` (if exists — tech context, patterns, testing)
   - Use defaults: `output_path` = `docs/working`
   - WARN: "No `.context/README.md` found. Using root README.md, AGENTS.md, and CLAUDE.md for context. A dedicated `.context/README.md` gives richer context."
c. If no context files found at all:
   - WARN: "No project context found. Proceeding without project context."
   - Use defaults: `output_path` = `docs/working`

Proceed to create the folder regardless of which tier resolved. Note in Step 7's confirmation which tier the context came from.

## Step 2: Get the Description

If `$ARGUMENTS` is empty or contains only whitespace:
- Ask the user: "What do you want to create? Describe the feature or document in a sentence or two."
- Wait for their response.

If a folder name was extracted from the first token (see format above), use the remaining text as the description. Otherwise, use the entire input as the description.

## Step 3: Analyze the Description

The README you produce becomes the identity card that every downstream skill reads — getting the scope, requirements, and affected areas right here prevents compounding errors in research, planning, outlining, and drafting.

Before deriving a name, analyze the description to extract:
- **Subject**: What this is called — the feature or the document
- **Purpose**: Why it's being created (new capability, refactor, bugfix, optimization, migration; or inform, persuade, educate, report)
- **Type**: New feature, enhancement, refactor, bugfix, integration; or report, guide, proposal, analysis, reference
- **Affected areas**: For code, which parts of the codebase this will touch. For a document, which sources or subject areas it covers. Inferred from context + description.
- **Audience signals**: Who this serves — the feature's users, or the document's readers
- **Scope signals**: Any explicit inclusions or exclusions

## Step 4: Derive the Folder Name

**ultrathink** — Naming requires weighing existing naming conventions, potential collisions with established modules, and future discoverability. A poorly-chosen name becomes a permanent API surface.

From the analysis, extract the 2-5 most meaningful keywords:

1. Convert to lowercase
2. Remove articles and filler prepositions unless meaningful
3. Replace spaces/underscores with hyphens
4. Remove non-alphanumeric characters (except hyphens)
5. Collapse consecutive hyphens
6. Truncate to 50 characters at a word boundary
7. Prefix the creation date. Obtain today's date with `date +%F` — run it; do not recall it. A
   wrong-but-plausible date is invisible on inspection, because nothing about `2026-07-31-foo`
   looks incorrect. Prepend it as `YYYY-MM-DD-`:

     api-rate-limiting  →  2026-08-01-api-rate-limiting

   If the name already begins with `YYYY-MM-DD-`, it is already dated. Leave it alone. This
   applies to a folder name the user supplies explicitly as well as to one you derive.

The leading position in every folder name is the creation date. Nothing else may occupy it —
never a sequence number such as `001-` or `002-`. If the working root already contains
sequentially-numbered folders, they are legacy artifacts of another tool; do not imitate them.
Chronological ordering comes from the date prefix, which sorts lexicographically, so a sequence
number would add nothing and would displace the date.

Step 6 truncates the INFERRED portion to 50 characters. The 11-character date prefix is added
after truncation, so the longest name is 61 characters — inside the 64-character ceiling.

The date records when the folder was CREATED. Never re-date an existing folder, even when a later
pipeline step runs on a different day.

Examples (the date shown is illustrative — use the actual output of `date +%F`, here 2026-08-01):
- "User authentication with OAuth2 and Google login" → `2026-08-01-user-auth-oauth2`
- "Add rate limiting to the API" → `2026-08-01-api-rate-limiting`
- "Fix the race condition in WebSocket reconnection" → `2026-08-01-websocket-reconnect-fix`
- "Q1 2026 Quarterly Report for the Board" → `2026-08-01-q1-2026-quarterly-report`
- "Product Roadmap" → `2026-08-01-product-roadmap`
- "The Getting Started Guide" → `2026-08-01-getting-started-guide`

## Step 5: Check for Conflicts

Check if `<output_root>/<derived-name>/` already exists. Compare the FULL dated name, not the inferred portion — `2026-08-01-api-cache` and `2026-09-15-api-cache` are different folders and neither collides with the other.

If it exists, use AskUserQuestion:
- "Use existing folder" — proceed (do not overwrite README.md)
- "Choose a different name" — ask for a new name

Because the name carries today's date, this check now fires only on a genuine same-day duplicate — almost always resumed work on something created earlier today. Reusing an inferred name on a later day produces a different folder and is not a collision.

One root means one namespace, so this check catches every collision — there is no second root a name could quietly land in instead.

## Step 6: Create Folder and README.md

1. `mkdir -p <output_root>/<derived-name>/`
2. Write `<output_root>/<derived-name>/README.md` using the **Folder Identity Template** in `references/manifest-update.md`. That reference is the canonical template — read it rather than reconstructing the shape from memory. It defines the frontmatter, an H1, and the sections `## Description`, `## Requirements`, `## Scope`, `## Affected Areas`, `## Audience`, and a 3-item `## Status` (Research / In progress / Complete). The frontmatter `title` is the full dated folder name (`2026-08-01-api-rate-limiting`), not the inferred portion alone; the H1 is the human-readable title and carries no date. Note in this step's confirmation which context tier (a/b/c from Step 1) the enriching content came from.

Write real content, not placeholders. The README is the folder's identity card — every subsequent skill reads it. Where a section applies less directly to this folder's work (for example `## Requirements` for a reference document), write a one-line note rather than deleting the heading, so every folder keeps the same shape.

**Voice.** Read `references/voice.md` before writing and apply its core rules — most visibly, define each term where it first appears. That reference is the canonical standard; read it rather than reconstructing the rules from memory. The folder README is a working artifact, so the deliverable overlay does not apply. Skip the pre-write verification step: a README this short has no room to drift.

Note: Other specification artifacts may exist in this folder (from SpecKit or other tools) and can provide additional context.

### Validate README Completeness

After generating the README.md, verify semantic completeness:

- [ ] Description is specific to this folder (not generic)
- [ ] Requirements are actionable (each could become a plan phase or a coverage target)
- [ ] Scope states both what is in and what is out
- [ ] Affected Areas reference real paths, architectural layers, or named sources
- [ ] Audience names who this serves, narrowed from the context file
- [ ] Every term, abbreviation, or borrowed concept is defined where it first appears
- [ ] Status checklist has all three items, all unchecked
- [ ] No placeholder text remains ("[TBD]", "TODO", etc.)
- [ ] Folder name begins with today's date in `YYYY-MM-DD` form
- [ ] Folder name has no sequential numeric prefix (`001-`, `002-`)

IF any check fails: revise the README before proceeding.

## Step 7: Confirm and Guide

Tell the user:
```
Created: <output_root>/<derived-name>/
Identity: <output_root>/<derived-name>/README.md

Next steps:
  /ai-research <derived-name>   — research the codebase or a topic
  /ai-plan <derived-name>       — create an implementation plan
  /ai-implement <derived-name>  — build from a plan

Manual steps (not yet migrated into this repository as skills):
  design the architecture — describe the architecture by hand; ai-architect has not migrated here
  structure a document     — outline the document by hand; ai-outline has not migrated here
  write the full document  — draft the document by hand; ai-draft has not migrated here
```

Print the full dated folder name in every command above — that is what was created. Downstream skills also resolve the short name (the inferred portion without the date), so either form works; the dated name is unambiguous.

Every step is optional. Run the ones the work calls for.

## Step 8: Manifest Update

After creating the folder, update the working manifest at `<output_root>/README.md` following the algorithm in `references/manifest-update.md`:

1. Read `<output_root>/README.md` (create from the template in that reference if missing)
2. Read the new folder's README.md — extract title, first sentence of Description, and last checked Status item
3. Append a new row to the table (maintain alphabetical order — for `YYYY-MM-DD-` names this is also chronological order, oldest first; undated legacy rows sort after dated ones because digits precede letters in ASCII)
4. Determine the state emoji from the 4-state ladder in that reference — a folder with only a README is `🆕 Created`
5. Add the row: `| [<folder>](<folder>/) | <emoji> <State> | <description> |`
6. Update the "Last updated" date in the blockquote
7. Write back with the Edit tool (preserve all other rows unchanged)
