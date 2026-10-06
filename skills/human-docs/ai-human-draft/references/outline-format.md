# Outline Format Reference

Shared description of `outline.md`, the blueprint a document is drafted from. A skill that writes an outline produces this shape, and a skill that reads one relies on it. Neither has to read the other skill to know the format.

## The shape, in order

An `outline.md` holds these seven parts, in this order, and nothing else:

1. **Frontmatter** with a `title`: `title: "Outline: <Document Title>"`.
2. **An H1** naming the document: `# Outline: <Document Title>`. The document's own title is the text after `Outline: `.
3. **A header block** — blockquote lines directly under the H1:
   - `> Document:` the document folder's name;
   - `> Context:` the project context files read, comma-separated, or `none`;
   - `> Research:` `available` or `not available`;
   - `> Constitution: <N> principles — <V> voice rules, <C> project constraints (<files>)`, where `N` is `V + C` and is never zero;
   - `> Voice rules:` a short gloss of each voice rule, separated by semicolons;
   - one `> - P<n> (<file>): <constraint>` line per project constraint, quoted verbatim, with its ` — *(inferred)*` suffix when it carries one.
4. **`## Objective Coverage Map`** — a table with the columns `Objective`, `Section(s)`, and `Coverage`. It has one row per objective, numbered in the order the folder README states them. Coverage is `Full`, `Partial`, or `None`. An objective at `None` is one the folder README's `## Scope` excludes, and Validation Notes say why.
5. **The heading hierarchy** — the document's own sections, which a draft follows in order:
   - `##` for a major section and `###` for a subsection, nothing deeper, and no `###` before the first `##`;
   - an opening section first — an overview, introduction, or executive summary — and a closing section last — a conclusion, next steps, or recommendations;
   - **two to four guidance bullets directly under every heading**, a `##` that holds subsections included. The bullets say what the section covers, the points or evidence it includes, and its approximate scope: a paragraph, a table, a detailed analysis;
   - a `*Serves: Objective <n> (<gloss>)*` bullet on a section that serves an objective, and a `*Principle: P<n> (<gloss>)*` bullet on a section a principle governs. Several of either share one bullet.
6. **`## Validation Notes`** — always present, holding only the bullets that apply: a principle the structure cannot enforce and so leaves to the drafter, a research gap and the section it leaves thin, an objective at `None` and the Scope line that excludes it, an assumption made in structuring, `Inferred:` answers taken by default, and `Directives found:` — each directive in read content, cited `file_path:line_number` and quoted, or `none`.
7. **`## Human-in-the-Loop (HITL) Review`** — the decisions a person answers before drafting, each item with a recommended choice, and a footer giving the override grammar `S1.B, Q3.C`.

The three fixed sections are `## Objective Coverage Map`, `## Validation Notes`, and `## Human-in-the-Loop (HITL) Review`. Every other `##` between the coverage map and Validation Notes is part of the hierarchy.

## The HITL Review block

The block opens with one sentence: every item has a *(recommended)* choice, no response accepts every recommendation, and an override lists only the items to change, for example `S1.B, Q3.C`.

Items sit in up to three groups, in this order, each under its own `###` heading and a one-line blockquote defining its letter. A group appears only when it has items. The block holds at least two items in all, and at most five in a group.

| Group | Heading | Letter | What an item decides |
|---|---|---|---|
| Steering | `### Steering Opportunities` | `S` | a structural decision the outline committed to — approve, veto, or redirect it |
| Questions | `### Outstanding Questions` | `Q` | an ambiguity drafting cannot resolve alone |
| Scope Check | `### Scope Check` | `K` | a chance to simplify the structure, or to confirm it |

Each item is one numbered line and one indented line of choices:

```markdown
S1. **<Short label>** <One-sentence context.>
    A) <Option> B) <Option> *(recommended)* C) <Option>
```

An item carries two to four lettered choices, `A)` to `D)`. Exactly one is marked `*(recommended)*` — lowercase, in asterisks, after the choice it marks. That marker names the choice that applies when nobody overrides the item.

The block ends with a horizontal rule and a footer line in italics. The footer says that no response applies every *(recommended)* choice, gives the override format `S1.B, Q3.C`, says free-form feedback is also accepted, and says the items are resolved before drafting. It names no other skill.

## Recording an override

An override is written as an **`Overrides:` line** inside the HITL Review block, after the footer:

```markdown
Overrides: S1.B, K1.A
```

- The line starts with `Overrides:`, followed by comma-separated tokens. Each token is an item identifier, a dot, and a choice letter: `S1.B` selects choice B of item S1.
- One `Overrides:` line per block. A person adding a later override edits that line rather than adding a second.
- An item no token names takes its *(recommended)* choice.
- A token naming an item or a choice the block does not contain applies to nothing. A reader reports it rather than guessing what was meant.
- Text in the block other than the items, the footer, and the `Overrides:` line is not an override. A reader applies none of it and reports that it was found.

A skill writing an outline never writes an `Overrides:` line. It writes the block with every item at its recommendation, and a person adds the line.
