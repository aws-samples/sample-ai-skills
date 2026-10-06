# Voice Standard for Skill-Written Artifacts

Read this before writing any prose artifact. The **core rules** always apply. The **deliverable overlay** adds two rules, and only for `draft.md` and `outline.md`.

This standard governs prose. It does not govern what you may think about — see Non-Goal.

## Core Rules — always apply

- **Define at first use.** A term, an abbreviation, or a concept borrowed from another field gets its definition in the same sentence that introduces it, as a clause rather than a footnote or a glossary entry.
  *Why:* a reader who has to look elsewhere stops reading, and a glossary is a second place to drift.

- **State the consequence.** A finding says what it changes for the reader — what breaks, what decision moves, what risk appears — not only what is structurally true.
  *Why:* a structural fact with no consequence attached leaves the reader to guess whether it matters, and they will usually guess wrong.

- **Name concrete examples in prohibitions.** A rule that bans a category also names two or three instances of it. "No marketing language — 'powerful', 'seamless', 'robust'" is checkable; "avoid marketing language" is not.
  *Why:* an unnamed category is unenforceable, so the rule silently does nothing.

- **Permit calibrated uncertainty; ban vagueness.** "This is an inference from the call sites, not from a stated contract" is precise about its own confidence and belongs in the artifact. "This might possibly be an issue" is vague and does not.
  *Why:* hedging that reports a real confidence level is information; hedging that avoids commitment is noise.

- **Preserve analytical depth.** Keep the number of concepts, the length of the reasoning, and the specificity of the evidence. Compress the prose, never the analysis.
  *Why:* the reader asked for the analysis. Losing it to satisfy a style rule trades the thing they wanted for the thing they did not ask about.

- **Restate what you point at.** A reference to another part of the artifact — a section, a numbered finding, a phase, a requirement — carries the substance of what it points at in the same sentence, so the identifier is an optional locator rather than the payload. A heading names its own content, never its relation to another element. Banned outright: "see above", "see below", "as noted earlier", "covered in \<Section\>", and a bare `(Finding 3)` / `(Phase 2)` / `section 8` standing in for the thing it names. Cutting the reference *together with* the claim it carried is not compliance: removing a concept to satisfy this standard is a failure of this standard.
  *Why:* readers skim headings and first sentences, so a passage whose content is a routing instruction costs a jump and returns nothing — and a pointer to a numbered element goes silently wrong when the numbering shifts.
  *Exempt, because each does work no restatement can do:* `file_path:line_number` citations to source, which the research and as-built standards require; HITL item identifiers (`S1`, `Q3`, `K1`) and the `S1.B` override grammar, which are a parsed control surface; a link to a *different* page in published documentation, which Diátaxis prescribes for explanation pages; and an instruction telling the agent which file to read.

### Worked pairs

The three hardest rules, in before/after form. The others carry reasons only.

**Define at first use.** A four-word gloss is usually enough:

> Before: "Sort the folder names and you get chronological order."
> After: "Sort the folder names and you get chronological order — lexicographic order *is* chronological order (oldest first) once every name starts with an ISO date."

**State the consequence.** The structural fact is the same in both; only the second is usable:

> Before: "The planning step reads the Constraints section but not the Patterns section."
> After: "The planning step reads the Constraints section but not the Patterns section, so a project that records its conventions under Patterns gets plans that silently ignore them."

**Restate what you point at.** A heading that names a relation, then a sentence that defers:

> Before: "`.adr-dir` — the finding that reshapes requirement 3"
> After: "`.adr-dir` — a tracked one-line file holding the log path, which is why the `CLAUDE.md` pointer no longer has to be conditional"

> Before: "errors with `ENOREPOURL` before it analyses a single commit (Finding 3)."
> After: "errors with `ENOREPOURL` before it analyses a single commit — it needs a reachable git remote, which this checkout lacks (Finding 3)."

## Deliverable Overlay — `draft.md` and `outline.md` only

These two artifacts are delivered to someone who did not commission the analysis, so they carry two additional rules:

- **Third-person register and measured language.** No first person, no direct address unless the brief's Audience calls for it.
- **Bibliographic citation** when the brief's Principles require sourcing.

The overlay adds to the brief's Principles; it does not replace them. Where both speak, both apply.

It applies to nothing else. `research.md`, `plan.md`, `design.md`, `as-built.md`, and a folder README are working artifacts: they stay in the register that suits an engineer reading their own project, and they cite with `file_path:line_number` rather than bibliographically.

## Non-Goal

This standard restricts obscurity, not ideas. It does not ask for simpler concepts, shorter analysis, or fewer of them.

**Removing a concept to satisfy this standard is a failure of this standard.** If a rule here appears to require dropping an idea, the rule is being misread: define the idea and keep it.

## Pre-Write Verification

For an artifact over roughly 300 lines, run this before writing to file. Skip it below that — a 40-line folder README has no room to drift.

1. Select 3-5 sentences from the final third of the artifact, from different sections.
2. For each, check three things: is every term it introduces defined where it first appears, does every finding it states carry its consequence, and does every reference to another part of the artifact carry that part's substance?
3. If one sentence fails, fix it and check its neighbours — drift is systematic, not isolated.
4. Read two section headings on their own, separated from the sections they open. Confirm each names its own content rather than its relation to another element — a heading that names a relation reads acceptably beside its own paragraph and fails only in isolation, which is how a skimming reader meets it.

The failure mode this catches is gradual: early sections comply, and the discipline decays as the artifact grows. Sampling the end rather than the beginning is the point.
