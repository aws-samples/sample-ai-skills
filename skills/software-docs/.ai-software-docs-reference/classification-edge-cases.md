# Classification Edge Cases

The rules for classifying pages that already exist. ASSESS, SURVEY, and ADOPT read this file; CREATE does not, because a request is not a page. The compass reference supplies the modes and their criteria, and this file supplies what changes when the input is a file on disk.

## 1. Rejected practices

Source: <https://diataxis.fr/how-to-use-diataxis/>

**The anti-scaffold rule.** Diátaxis names creating the four empty mode directories up front as the practice to avoid. Getting started "certainly does not mean that you should create empty structures for tutorials/howto guides/reference/explanation" — structures "with nothing in them." Then: "Don't do that. It's horrible."

**Its scope is projects that already have documentation.** The rule sits inside an improvement cycle whose first step is "**Choose something** - any piece of the documentation," which presupposes documentation to choose from. The source is silent on a project that has none.

**Its spirit is broader than its letter.** "**Diátaxis changes the structure of your documentation from the inside**," and "Good structure develops from within." A skill that stands a mode tree up ahead of the pages that would have created it works against that, whether or not the directories are empty. So:

- FIRST RUN, which seeds four mode directories in a project with no documentation, deviates knowingly, in a case the source does not reach. Never tell the user Diátaxis endorses it. The argument for it is this collection's own: a person cannot adopt a structure they have never seen, and every directory it creates ships with a page in it.
- ADOPT, which meets a project that already has pages, obeys the rule in full. It creates a mode directory only when a confirmed move puts a page in it, because four seeded directories beside unfiled pages would give the tree two organising schemes with every real page outside the new one.

**Do not split on intuition.** Because "sometimes intuition provides an immediate answer that is also wrong," never rewrite, split, or move a page on classification confidence alone. Stop and ask: that is the conflation gate.

## 2. What classification can and cannot check

Source: <https://diataxis.fr/quality/>

Diátaxis does not judge whether documentation is good: "**Diátaxis cannot address functional quality in documentation.**" Functional quality — "accuracy, completeness, consistency, usefulness, precision" — is exposed by Diátaxis but judged elsewhere; its role there "can have only an _analytical_ role." State the reach honestly in every report.

**Can check (structural):**

- the mode assignment, against the compass and each mode's require and forbid lists;
- one mode per page — the conflation gate;
- the title rules: a how-to begins "How to"; an explanation passes the implicit-"About" test;
- that the page has the sections of its mode's template;
- that no `{placeholder}` remains outside a fenced code block;
- that the page sits in the directory of the mode it serves.

**Cannot check (functional):** whether a tutorial teaches, whether a how-to's steps work, whether reference is accurate or complete, whether an explanation is correct or illuminating. Never claim a run verified any of these.

**Product-mirroring reference is correct, not a defect.** Reference "should mirror the structure of the product," so a `reference/` tree subdivided the way the product is subdivided is reference done right. SURVEY ranks such pages low rather than flagging them.

## 3. The thin-page signal

Anchored on The Good Docs Project's published caps only — step count and completion time. There is no published word-count rule; do not invent one or attribute one to Good Docs.

- **How-to.** `how-to/guide_how-to.md` (Good Docs, tag v1.6.0): "Focus only on one task in your how-to and restrict to a maximum of 8-10 steps per task." Over ten steps is a candidate for splitting into sub-tasks; one step is a candidate thin page. Count steps.
- **Tutorial.** `tutorial/guide_tutorial.md` (Good Docs, tag v1.6.0): "Ideally, your tutorial should take 15 to 60 minutes to complete." Estimate from the step and section count, not the word count.

Report a thin page as a weak signal for a person, never as a failure.

## 4. Connective pages — the directory-index rule

**This is not Diátaxis doctrine.** Diátaxis has four modes and no fifth. This collection adds *connective* as a label for a page whose job is to route a reader rather than to teach, instruct, describe, or explain. Such a page legitimately carries fragments of several modes, so classifying it would report a conflation that is not one.

**The rule is a filename and nothing else.** A page is connective when its filename is `README.md` or `index.md`. That is the whole test: not the page's content, and not an assessment of its purpose. A page that reads like a router but is named `overview.md` is classified normally. A page named `index.md` is connective even if its prose reads as explanation. A run reasoning about whether a page "is really doing routing" has left the rule and is making the judgment the rule exists to remove.

**The category is closed.** No other page is connective, and no page earns the label by resembling one. Connective pages are never classified, never enter the conflation gate, never count as unfiled, and never move.

## 5. Fence-aware heading extraction

Classification reads a page's headings, and a naive scan for lines beginning `## ` is wrong wherever a page shows example headings inside fenced code blocks — scaffolds the page documents, not headings the page has.

**Rule:** when collecting a page's own headings or frontmatter, ignore every line between a fence opening (three or more backticks, or three or more tildes) and its matching close. Only lines outside fences count.

**Worked example.** A how-to page on writing a changelog has two real headings, `## Before you start` and `## Write the entry`. Between them it shows the reader a changelog skeleton in a fence, which holds `## Added`, `## Fixed`, and `## Changed`. A naive scan reports five headings, three of them the vocabulary of a reference page; a fence-aware scan reports two. A classification built on the naive count reads a clean how-to as a how-to and reference conflation.
