---
name: ai-make-skill
description: "Write a new agent skill, from a description or from work already done in the conversation, as an Agent Skills folder: a SKILL.md plus the references/, scripts/, or assets/ it needs. Detects which agent the skill is for and always confirms it, asks only what the request leaves open, writes standard frontmatter plus only the keys a confirmed agent reads, and verifies the written files on disk. Invoke ONLY via the /ai-make-skill slash command. Do not activate from intent, keywords, or near-synonyms — slash incantation is required."
disallowed-tools: "WebFetch, WebSearch, Skill, NotebookEdit, Agent"
allowed-tools: "Bash(git rev-parse:*), Bash(test:*), Bash(wc:*)"
disable-model-invocation: true
effort: high
---

# /ai-make-skill — Write a New Agent Skill

This skill writes one new skill as an [Agent Skills](https://agentskills.io) folder: a `SKILL.md`,
plus the `references/`, `scripts/`, and `assets/` subdirectories the request needs. The written skill
follows the standard by default. A frontmatter key or a file that only one agent reads is added only
for an agent the user has confirmed, and is labelled with that agent, so a skill written for no agent
in particular is valid under the standard alone.

Run this skill only when the user invokes it by name. Do not start it because a request looks like a
request for a new skill.

The workflow: detect the agent and confirm it, fill in what the request already answers, ask the rest
in one batch, confirm a summary and the output directory, write, verify the files on disk, report.

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

## Input

The input is a description of the skill to write, or a request to turn work already done in this
conversation into a skill.

| Input | What it selects |
|---|---|
| a description — "a skill that converts a CSV to a formatted table" | Step 2 takes every choice the description answers and asks about the rest. |
| a reference to the conversation — "turn what we just did into a skill" | Step 2 takes the steps, the tools used, the corrections the user made, and the input and output forms from the conversation, and asks only what it leaves open. |
| nothing | Ask what the skill should do, in one sentence, before anything else. Nothing is detected, asked, or written until the user answers. |

```text
$ARGUMENTS
```

If the block above holds a placeholder rather than the user's text, your agent does not substitute
it: take the input from the message that invoked this skill.

## What this skill knows about agents

This skill holds one table about agents, and uses it only to suggest which agent is meant. The table
is a hint, and a row may go stale. A stale row costs a worse suggestion, never a wrong file, because
every fact that shapes the written folder is asked for.

| Agent | Environment variable that identifies it | Configuration directory |
|---|---|---|
| Claude Code | `CLAUDECODE` | `.claude/` |
| Codex | none known | `.agents/` |
| Cursor | none known | `.cursor/` |
| Kiro | none known | `.kiro/` |
| OpenCode | none known | `.opencode/` |
| pi | `PI_CODING_AGENT` | `.pi/` |

Every other agent fact comes from the user. There are four:

1. **Frontmatter keys** — which keys outside the standard the agent reads, and the value of each.
2. **Invocation form** — how a user invokes a skill by name under that agent, and whether the agent
   replaces a placeholder in the body with the text typed after the name.
3. **Additional files** — any file the agent needs beside `SKILL.md`, for example one that turns
   automatic activation off.
4. **Skills directory** — where the agent reads skills from. It becomes the suggested answer to the
   output-directory question in Step 3, and nothing more.

Do not look any of these up: not in the agent's documentation, not in an installer's or another
tool's configuration, and not by copying another skill's frontmatter. A fact the user gave is one the
user can check in the report; a fact you found is one nobody confirmed. An agent the table does not
list is no reason to stop — proceed on the user's answers.

## Step 1: Detect the agent, then confirm it

Detection finds which agent is running this skill, or which agents the repository is set up for. The
question that matters is which agent the new skill is *for*, and the answers differ whenever someone
writes a skill for an agent other than the one they are using. So detection only suggests an answer,
and the question is always asked, even when exactly one candidate was found.

1. **Environment.** For each row naming a variable, check whether it is set, one name at a time —
   `test -n "$CLAUDECODE"` exits 0 when it is. Never print the whole environment: it holds
   credentials. If any variable is set, its agents are the candidates and step 2 is skipped.
2. **Directories.** Only when step 1 found nothing: take the root from `git rev-parse
   --show-toplevel`, or the working directory outside a repository, and check each row's directory
   there with `test -d`. Every directory present names a candidate.
3. **Report and ask**, in one message: what step 1 found, naming each variable that was set and its
   agent; what step 2 found, or that it was skipped. Then ask whether to write for the detected
   agent, for a different agent, or for several. With no candidate, ask which agent or agents to
   write for, and offer *the Agent Skills standard, with no agent-specific additions* as an answer.

When the request already names the agent or agents, the question confirms that answer against what
detection found rather than asking it afresh.

With two or more candidates, list them all and pick none. Table order, alphabetical order, and which
directory changed last say nothing about which agent the skill is for. The answer can name an agent
detection did not find; detection then changes nothing.

If the user does not answer, stop. Nothing is written.

**Example**, in a repository holding `.claude/` and `.kiro/`, with neither variable set:

> No agent environment variable is set. The repository has `.claude/` (Claude Code) and `.kiro/`
> (Kiro). Write the skill for Claude Code, for Kiro, for both, for another agent, or for the Agent
> Skills standard with no agent-specific additions?

## Step 2: Fill in what the request answers, then ask the rest

Take every choice the request already answers — and, when the request refers to this conversation,
every choice the conversation answers: the steps, the tools used, the corrections the user made, the
input and output forms. Do not ask about any of those again.

Ask about everything left in one batch. Each question states the default that applies if it goes
unanswered, and offers that default as the recommended answer, so a user who answers only some of them
still gets a predictable skill. An answer that does not address its question leaves the question
unanswered: take the default rather than asking again.

| Choice | Default when unanswered | Ask when |
|---|---|---|
| Name | derived from the action the skill performs | the request names none |
| Description | written from the request's wording: what the skill does, then when to use it | the request does not say when the skill should be used |
| Activation | automatic: an agent may start the skill when a request matches its description | the request does not say whether it runs only when invoked by name |
| Input: what it is | none, and no input section is written | the request suggests the skill acts on something supplied with it |
| Input: what each form selects | one form, handled one way | the input can take more than one form — a path, a description, a flag |
| Input: when it is empty | ask the user for the input, and stop until answered | the skill takes input |
| Editing boundary | none: no `## Edit Scope` section is written | the request does not say whether the skill's writes stay inside the working directory |
| Optional standard fields | none of `license`, `compatibility`, `metadata`, `allowed-tools` | the request mentions a license, a runtime requirement, or the tools the skill needs; otherwise they are listed in the summary as available |
| Agent facts, per confirmed agent | the standard form for each fact not given, reported as a gap | the user has not given the agent's frontmatter keys, invocation form, additional files, or skills directory |
| Bundled `scripts/` | none | the workflow runs the same deterministic code every time — a conversion, a validation, a chart |
| `references/` split | none, unless the body would reach 500 lines | the material is long, or only some runs need part of it |
| Output directory | | always, with the summary in Step 3 |

The output directory is the one choice with no default. Every candidate default is some agent's own
skills directory, and writing there unasked is installing.

**When the user does not know an agent fact**, write the standard form for that part and keep going.
Do not stop the run, and do not go and find the answer. Record each part left out, and where it would
go, for the report:

- **Invocation form unknown** — state the restriction in the body in plain prose, "Run this skill only
  when the user invokes it by name", with no agent-specific syntax.
- **Additional file unknown** — write none, and record that explicit-only invocation is stated in the
  body and not enforced.
- **Frontmatter keys unknown** — write the standard fields only.

## Step 3: Confirm the summary and the output directory

Present every choice — derived, answered, and defaulted, each marked as which — and in the same message
ask where to write the folder. Write nothing until the user confirms both. When the user changes an
answer, present the whole summary again with the change, and wait for confirmation again.

- **The output directory is asked on every run.** When an agent is confirmed and the user gave its
  skills directory, offer that directory as the suggested answer, and still ask. When the request
  already names a directory, the summary states it, and confirming the summary answers the question.
  If the question goes unanswered, stop: nothing is written, and no built-in path is used in its place.
- **Writing is not installing.** Never place the folder in an agent's skills directory because that
  agent reads it — only because the user named that directory as the answer.
- **The folder is `<output directory>/<name>/`.** If the answer ends in a directory whose name is not
  the skill's `name`, say so and ask which of the two to change. Never write a folder whose name and
  `name` disagree.
- **Several agents produce one folder each**, each carrying only that agent's keys, invocation form,
  and additional files, as the user gave them. When two answers would place two folders at one path,
  report the collision and ask. The second never overwrites the first.
- **An existing folder is never overwritten unasked.** If `<output directory>/<name>/` already exists,
  say so and ask.

Print every path as an absolute path. A path outside the working directory is written only because the
user named it in this answer, per Edit Scope.

## Step 4: Write the skill

### The frontmatter

Write the two required fields, then only what the summary added:

- `name` — lowercase letters, digits, and hyphens; at most 64 characters; no leading, trailing, or
  doubled hyphen; equal to the folder's name.
- `description` — what the skill does, then when to use it, in at most 1024 characters. An agent that
  activates skills automatically matches requests against this text, so name the phrases, file types,
  and situations that should start the skill, and what it is not for when a near-miss is likely. For a
  skill that runs only when invoked by name, end the description by saying so.
- `license`, `compatibility`, `metadata`, `allowed-tools` — only when the summary includes them.
- **A key only one agent reads** — only in that agent's folder, and only when the user confirmed the
  agent and gave the key. Put a comment line naming the agent directly above the keys it reads, as
  `# <agent> reads: <key>, <key>`, on its own line and holding a colon. Some frontmatter readers split
  every line at its first colon and reject a line with none, and a comment written after a value
  becomes part of that value for them.

A key that turns automatic activation off fails open: an agent that ignores the key activates the
skill automatically. Whenever you write such a key, also state the restriction in the body (below), so
the guarantee survives an agent that does not read the key.

**Example**, for an agent the user named as Acme, which they said reads a key `run-mode`. The agent
and the key are illustrations; real ones come from the user:

```yaml
---
name: csv-to-table
description: "Convert a CSV file into a Markdown table with aligned columns and a header row. Use when the user asks to tabulate, format, or preview CSV data. Not for spreadsheets with formulas. Runs only when invoked by name."
# Acme reads: run-mode
run-mode: explicit
---
```

### The body

Write the body for the agent that will follow it.

- **Explain why, not only what.** An instruction with its reason carries over to the case it did not
  name; an all-capitals ALWAYS or NEVER does not. Keep capitals for real safety limits.
- **Lead with a one-paragraph purpose, then numbered steps.** Detail, examples, and edge cases go under
  the step they belong to, or into `references/`.
- **Give at least one concrete example per step** — an input and the output it produces.
- **State the output format exactly** — which files, which sections, in what order.
- **Say what to do when something goes wrong** — a malformed input, a missing file, an ambiguous
  request. Asking is better than guessing or dropping data without saying so.
- **Stay under 500 lines.** Near that, move detail into `references/` and add one line per reference
  file saying when to read it. Cite each in backticks or as a Markdown link, so Step 5 finds it.
- **Bundle a script only for code that never varies**, and state the exact command that runs it, with
  its options. A script beats prose when every run would otherwise write the same helper again.
- **Name capabilities, not one agent's tools** — "read the file", "run the command" — except in a
  passage labelled with the agent that reads it.
- **Title the body with the skill's name**, as in `# csv-to-table — Convert a CSV File`. Invocation
  syntax — a slash, a prefix — appears in the title or anywhere else only as the user gave it, in that
  agent's folder. This skill's own title and input block are not a template for the new one.

Then add each section the summary calls for:

- **Input.** When the skill takes input, a section stating in prose what the input is, what each form
  of it selects, and what happens when it is empty. The prose must work alone: an agent that does not
  substitute an argument placeholder leaves it as literal text, and a body that depends on the
  substitution then reads as though the input were already in hand. When the user said the confirmed
  agent substitutes a placeholder, put it in a fenced block after the prose, in that agent's folder
  only; otherwise write no placeholder at all. When the skill takes no input, write no input section
  and no placeholder.

  **Example** of the prose, for a skill taking a path, a description, or nothing:

  > The input is the CSV to convert. A path to a `.csv` file converts that file. A description of the
  > data — "the sales export in this folder" — finds the file it describes, and asks which when more
  > than one matches. No input lists the `.csv` files in the working directory and asks which to use.

- **Invocation.** When the skill runs only when invoked by name, a sentence in the body saying so. This
  is the body half of the fail-open rule above, and the whole restriction when the invocation form is
  unknown.
- **Editing boundary.** When the user confirmed it, copy this skill's own `## Edit Scope` section into
  the new body word for word. It confines writes to the working directory and leaves reads unrestricted.
  When the user declined, write no such section.

When a step of the new skill may need deep reasoning, read
[`references/reasoning-depth.md`](references/reasoning-depth.md) before writing that step.

## Step 5: Verify the files on disk

Re-read each `SKILL.md` you wrote from disk, not from the text you meant to write — a write that was cut
short shows only on disk — and assert each of these. Every failure names the file and the line.

1. **The frontmatter parses.** The first line is `---`, a later `---` line closes the block, and every
   line between is a YAML mapping entry, a continuation of one, or a comment.
2. **Both required fields are present** — `name` and `description`, neither empty.
3. **`name` equals the name of the folder** that holds the file.
4. **The body is under 500 lines** — every line after the closing `---`. Count with `wc -l` on the file
   and subtract the frontmatter's lines. At 500 or more, the remedy is moving detail into `references/`.
5. **Every cited `references/` path resolves to a file inside the written folder.** A missing file
   fails, naming the line that cites it; so does a path that leaves the folder, through `..` or as an
   absolute path.

Fix a failure you caused — a reference you meant to write and did not — and run all five again. If one
still fails, report it with the file and the line, and leave the files in place for the user.

Do not run any check command belonging to the repository you are in, even one that checks skills. Such
a command enforces that repository's own conventions, which this skill does not hold. The written skill
is accepted on the five assertions above, and is reported as written whatever such a command would say.

## Step 6: Report

End every run that wrote something with:

- every path written, absolute, one per line;
- each agent-specific value used, by agent — the keys and their values, the invocation form, the
  additional files — so a wrong value shows here and not only inside a file;
- every agent-specific part left out because the user did not know it, and where it would go;
- whether an editing boundary was written and, when it was not, that the skill states none;
- the result of each assertion in Step 5;
- at least two requests that should start the new skill. For a skill that runs only when invoked by
  name, give two invocations with realistic input.

**Example:**

```
written   /home/dev/project/skills/csv-to-table/SKILL.md
agent     Acme — run-mode: explicit (frontmatter); invocation form: not known
left out  Acme's invocation syntax — the restriction is prose in the body; add the syntax to the description
boundary  none: csv-to-table states no editing boundary
verified  frontmatter parses, name and description present, name = folder, 96 body lines, no references cited
try       invoke csv-to-table with "sales.csv"; invoke it with "the export in data/"
```

A run that stopped early — an unanswered question, a refused summary — ends by saying where it stopped
and that nothing was written.

## What this skill never does

- **Never writes before the summary and the output directory are confirmed.**
- **Never writes to a path the user did not give**, and never falls back to a default directory.
- **Never writes an agent-specific key, invocation form, or file** for an agent the user did not confirm.
- **Never fetches an agent's documentation** or reads another tool's configuration to fill a gap.
- **Never overwrites an existing folder** unasked, including one written earlier in the same run.
- **Never runs a repository's own check command.**
