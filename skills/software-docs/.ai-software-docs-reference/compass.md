# Diátaxis Compass

How to decide which of the four Diátaxis modes a request or a page serves, and which page template that mode uses. Every branch that classifies reads this file. Every normative claim carries the primary source it comes from, so a reader can confirm it rather than trust the paraphrase.

Diátaxis (Daniele Procida, <https://diataxis.fr>) sorts documentation into four modes: tutorial, how-to, reference, and explanation. The Good Docs Project (<https://thegooddocsproject.dev>) supplies the page templates. The two are independent projects; where this file maps one onto the other (explanation → Good Docs "concept"), that is this collection's synthesis, labelled as such.

## 1. The compass (Source: <https://diataxis.fr/compass/>)

To place any piece of documentation, ask **two questions**: "action or cognition? acquisition or application?" Then read the answer off this table, quoted from the compass page:

| If the content… | …and serves the user's… | …then it must belong to… |
|---|---|---|
| informs action | acquisition of skill | a tutorial |
| informs action | application of skill | a how-to guide |
| informs cognition | application of skill | reference |
| informs cognition | acquisition of skill | explanation |

Two cautions from the same page:

- **Use the terms flexibly.** The page says to "use the compass's terms flexibly" and "don't get fixated on the exact names." The axis matters more than the label.
- **Do not trust a fast answer.** "Worse, sometimes intuition provides an immediate answer that is also wrong." A confident first read is not evidence; check it against the require and forbid lists below.

## 2. The four modes — require and forbid

Each mode carries a **require** list (what its source page says the mode is) and a **forbid** list (what the same page says it must not do). These are the checkable criteria.

### Tutorial — learning-oriented (Source: <https://diataxis.fr/tutorials/>)

**Require:**

- "A tutorial is always **learning-oriented**"; it is "a _practical activity, in which the student learns by doing_."
- "A tutorial in other words is a lesson" — "a kind of contract between teacher and student, in which nearly all the responsibility falls upon the teacher."
- The exercise must be "_meaningful_", "_successful_" (the pupil can complete it), "_logical_" (the path makes sense), and "_usefully complete_."
- "A tutorial must inspire confidence" — "your tutorial works for every user, every time."

**Forbid** — the page's four "anti-pedagogical temptations": "abstraction, generalisation", "explanation", "choices", "information." Specifically:

- Not a how-to: "Its purpose is not to help the user get something done, but to help them learn."
- No explanation inline: "_A tutorial is not the place for explanation._" Instead "provide a link or reference to that explanation."
- No options or alternatives: "Your guidance needs to remain focused on what's required to reach the conclusion."

### How-to guide — task-oriented (Source: <https://diataxis.fr/how-to-guides/>)

**Require** — the page's "How-to characteristics", verbatim: "focused on tasks or problems"; "assume the user knows what they want to achieve"; "action and only action"; "no digression, explanation, teaching." It "serves the work of the already-competent user"; it is "an executable solution to a real-world problem or task," and its "fundamental structure … is a sequence."

**Forbid** — teaching or explaining. "It's not the responsibility of a recipe to teach you how to make something"; a good recipe "excludes both teaching and discussion." If concepts or reference matter, "link to them."

**Bounded permission — do not over-enforce.** A how-to need not be one rigid line: "The sequences of action in a how-to guide sometimes need to fork and overlap, and they have multiple entry and exit-points." A guide that branches is still a valid how-to.

### Reference — information-oriented (Source: <https://diataxis.fr/reference/>)

**Require:**

- "Reference material is **information-oriented**." It gives "technical descriptions of the machinery and how to operate it."
- "It should be **austere**"; "neutrality, objectivity, factuality."
- "One hardly _reads_ reference material; one _consults_ it."
- "There should be no doubt or ambiguity in reference; it should be wholly authoritative."
- Its structure mirrors the product: "the structure of the documentation should mirror the structure of the product." So a reference subdirectory per component of the product is reference done right, not a defect.

**Forbid** — how-to, explanation, and opinion: "explain, instruct, discuss, opine, and all these things run counter to the needs of technical reference." "Instead, link to how-to guides, explanation and introductory tutorials."

**Bounded permission — do not over-enforce.** Reference may describe mechanism: "it can and often needs to include a description of how something works or the correct way to use it." A description of how something works does not by itself make a reference page a conflation. What reference must not do is *instruct* (steps to follow) or *explain the why* (discursive rationale).

### Explanation — understanding-oriented (Source: <https://diataxis.fr/explanation/>)

**Require:**

- "Explanation is a discursive treatment of a subject, that permits reflection." It is "understanding-oriented."
- It explains "why things are so - design decisions, historical reasons, technical constraints." It answers "Can you tell me about …?"
- **Work versus study.** Explanation "is documentation that it makes sense to read while away from the product itself" — "the only kind of documentation that it might make sense to read in the bath." Reference and how-to are consulted while working; explanation is read while studying, away from the product. That distance is the discriminator.

**Forbid** — instruction and bare description: "In explanation, you're not giving instruction or describing facts - you're opening up the topic for consideration." "Keep explanation closely bounded"; letting instruction or reference creep in "interferes with the explanation itself."

Do not use "could you disagree with this sentence" as an explanation test. It appears nowhere on the Diátaxis site; the work-versus-study distinction is the test.

## 3. Naming rules

Only two modes carry a title rule. Tutorial and reference carry none — do not invent one.

**How-to — a title must begin "How to".** Source: <https://diataxis.fr/how-to-guides/> — "Choose titles that say exactly what a how-to guide shows."

| Rung | Example | Why |
|---|---|---|
| good | "How to integrate application performance monitoring" | says exactly what it shows |
| bad | "Integrating application performance monitoring" | "maybe the document is about how to decide whether you should, not about how to do it" |
| very bad | "Application performance monitoring" | "maybe it's about how - but maybe it's about whether, or even just an explanation of what it is" |

**Explanation — the implicit "About" test.** Source: <https://diataxis.fr/explanation/> — "you should be able to place an implicit (or even explicit) about in front of each title." "About user authentication" and "About database connection policies" pass. A title that reads naturally after "About" is explanation-shaped.

## 4. Adjacency — where modes blur (Source: <https://diataxis.fr/map/>)

Neighbouring modes share a quality, so they bleed into each other, and a page near one of these boundaries is where conflation happens. "The different kinds of documentation bleed into each other," and the worst case is "a complete or partial collapse of tutorials and how-to guides into each other."

| Shared quality | Pair that blurs |
|---|---|
| "guide action" | tutorial ↔ how-to |
| "serve the application of skill" | how-to ↔ reference |
| "contain propositional knowledge" | reference ↔ explanation |
| "serve the acquisition of skill" | tutorial ↔ explanation |

Break a tie with the discriminator table from the same page:

| Mode | Answers the question | Form | Orientation |
|---|---|---|---|
| Tutorial | "Can you teach me to…?" | "a lesson" | learning |
| How-to | "How do I…?" | "a series of steps" | goals |
| Reference | "What is…?" | "dry description" | information |
| Explanation | "Why…?" | "discursive explanation" | understanding |

## 5. Difficulty is independent of mode (Source: <https://diataxis.fr/tutorials-how-to/>)

Do not split tutorial from how-to by how hard the material is. "A tutorial can present something complex or advanced. And, a how-to guide can cover something that's basic or well-known." "How-to guides can, do and often should cover basic procedures." The line is purpose: "The difference between the two lies in the need they serve: **the user's study**, or **their work**."

## 6. Templates

The page templates are The Good Docs Project's, tag v1.6.0, under MIT No Attribution (MIT-0), in `templates/` beside this file. One per mode:

| Diátaxis mode | Template | Note |
|---|---|---|
| tutorial | `tutorial.md` | direct |
| how-to | `how-to.md` | direct |
| how-to, troubleshooting a symptom | `troubleshooting.md` | a distinct page shape; Diátaxis classifies troubleshooting as how-to |
| reference | `reference.md` | direct |
| explanation | `concept.md` | **synthesis** — Good Docs has no explanation template, so explanation maps to its nearest fit, `concept` |

To turn a template into a page:

1. Keep its sections and their order. Delete a section the template marks optional when the page has nothing for it.
2. Fill every `{slot}` with real content, and delete every HTML comment, including the source header at the top — those are authoring notes. **A finished page contains no `{` character outside a fenced code block.**
3. Apply the title rule for the mode (§3).
4. Write in the voice standard's core rules, and use the project's own key terms where the project context set defines them.
