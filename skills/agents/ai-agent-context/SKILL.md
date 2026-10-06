---
name: ai-agent-context
description: "Write agent context documentation (CLAUDE.md + README.md) for a source code directory. Invoke ONLY via the /ai-agent-context slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
disable-model-invocation: true
effort: high
---

# Agent Code: Directory Context Documentation

You write directory-level context documentation — the CLAUDE.md + README.md pair that provides context to humans and AI assistants entering a source code directory.

## Edit Scope

Write only inside the repository or working directory this session was invoked in.
Creating, modifying, moving, or deleting anything outside it — a global agent
configuration such as `~/.claude/`, another repository or worktree, a dotfile in the
user's home directory, a system path such as `/etc` — requires the user to name that
path in their request. Reading outside it is unrestricted.

Temporary files are the one exemption. You may create a file or directory with
`mktemp` or `mktemp -d` under the system temporary directory — `$TMPDIR`, or `/tmp`
when it is unset — without the user naming it. Remove every file and directory you
created this way before you finish, including when you stop early. A fixed or
predictable name under the temporary directory is not exempt.

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

## Context Loading

1. Read the project context set: the root `README.md`, `AGENTS.md`, and `CLAUDE.md` when present — skipping a `CLAUDE.md` that is only the `@AGENTS.md` pointer — then each in-repository file listed in `context_files` in `.ai-skills.toml`, when that file exists
   - Extract Objectives, Constraints, Key Terms from whichever files carry them
   - Use these to inform CLAUDE.md content (e.g., if Constraints mention compliance requirements, note those in the directory's CLAUDE.md)

2. Accept target directory from the user via `$ARGUMENTS`

## Principles

1. **Deep-read, don't skim.** Read every file in the target directory — full implementations, not just signatures.
2. **Apply the content test.** For every candidate fact: "Would an AI assistant working in this directory make a mistake or waste time without knowing this?" Yes → CLAUDE.md. No but useful → README.md.
3. **Separate concerns.** CLAUDE.md is the grab-and-go cheat sheet. README.md is the structured reference. Never duplicate content between them.
4. **No empty sections.** Only include README.md sections that have content.
5. **Verify against source.** Every file name, path, env var, service name must be confirmed by reading the actual code.

## Process

1. **Accept target directory** from the user
2. **Read every file** in the directory (and immediate subdirectories if relevant). Read full content — trace function calls, identify external service wrappers, find env var reads, spot validation constraints.
3. **Identify grab-and-go facts** by scanning for these categories:

   **ultrathink** — False negatives in CLAUDE.md are costly — an AI assistant that doesn't know a critical constraint will violate it. Apply the content test rigorously across all categories below.

   - Service identity — which client, SDK, or API does this wrap?
   - IAM requirement — which policy or permissions are needed?
   - Required env vars — what must be set for the code to run?
   - Input constraints — what validation rules produce cryptic errors?
   - Consistency model — eventual vs immediate, caching behavior?
   - Auth mechanism — how does identity flow through the code?
   - Critical rules — what's easy to violate?
   - Project patterns — conventions from `CLAUDE.md` if present, or evident in the surrounding code, that apply to this directory
4. **Discover doc locations dynamically** — check for developer-docs directories. Do not hardcode paths.
5. **Write CLAUDE.md** following the template below
6. **Write README.md** following the template below
7. **Validate** using the checklist below

## CLAUDE.md Template

```markdown
# {directory-path}/

{One sentence: what lives here and its role in the system.}
{Optional second sentence: key technology or wrapper target.}

- {Fact: the thing you'd get wrong — wrong service name, wrong import}
- {Fact: the constraint that causes a runtime error — regex, env var, type}
- {Fact: the behavioral surprise — eventual consistency, missing API, side effect}

See README.md for {what the README covers}.
```

Rules:
- H1 header uses the directory path relative to the project root
- 3-8 lines of content (excluding H1). Maximum 10.
- Each bullet is a fact that prevents a mistake, not background information
- End with a pointer to README.md that names what it covers

## README.md Template

Include only sections that have content.

```markdown
# {Title}

{1-2 sentence description of what this directory contains and its purpose.}

## Contents

| File/Directory | Purpose |
|----------------|---------|
| `file.py` | Brief description |

## {Domain-Specific Section}

(Varies by directory type: routes table, API mapping, concepts, data flow)

## Known Quirks

(Hard-won debugging knowledge. Things that work differently than expected.)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|

## Integration Points

(How this code connects to the rest of the system.)

## Related

- See [CLAUDE.md](./CLAUDE.md) for conventions.
```

Rules:
- Use tables for structured data
- Use prose for narrative
- "Known Quirks" is highest-value when wrapping external services

## Validation Checklist

- [ ] CLAUDE.md is under 10 lines of content (excluding H1)
- [ ] CLAUDE.md contains only facts that prevent mistakes
- [ ] README.md is scannable in under 2 minutes
- [ ] README.md has no empty sections
- [ ] All file names match actual files in the directory
- [ ] All import paths are correct
- [ ] All env var names match what the code actually reads
- [ ] No content in CLAUDE.md that belongs in README.md
- [ ] CLAUDE.md pointer to README.md names specific content

## Scope

This skill applies to any codebase. It does NOT:
- Write docstrings
- Write published documentation site pages
- Decide whether a directory needs context docs — the user activates this skill
