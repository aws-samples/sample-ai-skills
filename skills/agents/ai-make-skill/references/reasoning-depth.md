# Reasoning depth

This file describes reasoning depth in agent-neutral terms and drops the three named thinking budgets
its predecessor listed, because those names and token counts belonged to one agent's keywords rather
than to the kinds of step that need depth; the one agent-specific directive left is in the passage
labelled Claude Code at the end.

Read it while writing a step of a new skill that may need deep reasoning. Most steps do not, and a
skill that asks for depth everywhere runs slower and gains nothing: mechanical workflows,
template-filling, and command dispatch should stay fast.

## Which steps need it

| Kind of step | Demand | Ask for deep reasoning? |
|---|---|---|
| File reads and writes — read, write, copy, create | low | no |
| Filling a template from answers already given | low | no |
| Formulating the questions to ask the user | medium | no |
| Dispatching a command — parsing arguments, running a tool | low | no |
| Transforming a format by applying rules systematically | medium | no |
| Gap detection — what a spec or a context leaves out | high | yes |
| Architecture analysis — how something fits an existing system | high | yes |
| Adversarial review — finding problems, conflicts, and risks | high | yes |
| Constraint checking — validating against several sources of rules at once | high | yes |
| Framing a decision for a person to review | high | yes |
| Synthesizing complex findings into a document or a plan | medium to high | consider it |

## When to ask for it

- Adversarial self-assessment: a review, a validation, a quality gate.
- Gap detection: completeness across several dimensions at once.
- Architecture analysis: tracing dependencies and integration points.
- Constraint checking: cross-referencing more than one rule source.
- Framing a decision for a person: reducing complex findings to the choices that need them.

## When not to

- File reads and writes.
- Filling a template from the user's answers.
- Formulating questions.
- Command dispatch, and any step a script could do.

The test: does shallow reasoning at this step produce an error that later steps build on? If it does,
ask for depth there. If a mistake would be visible and cheap to fix at once, do not.

## How to ask for it

Put one sentence immediately before the step, saying what goes wrong when the step is done shallowly.
Every agent reads a sentence, so this works whichever agent runs the skill:

```markdown
Take time over this step: a shallow review here ships a skill with trigger gaps and unexplained
constraints, and both degrade every later run.
```

Name the consequence, not the effort. "Think carefully" says nothing a model can act on; "a missed
requirement here is rebuilt after review" tells it what to look for.

## Claude Code only

Claude Code reads the word `ultrathink` in a skill body as a request for its deepest reasoning on that
turn. Write it only in a folder for Claude Code, and only before a step the table above marks *yes*.
Place it inline, immediately before the step, followed by the same one-sentence consequence:

```markdown
**ultrathink** — A shallow review here ships the skill with trigger gaps, unnecessary length, or
unexplained constraints, and each of them degrades every later run.
```

Other agents read the word as ordinary text, so in a folder for any other agent use the
agent-neutral sentence above instead.
