# Provenance: identity and ancestry

Background for two checks the base promote path **does not carry** and one it
does. `assets/promote_cli.py` performs no origin pairing and no ancestry
comparison; a repository that wants either writes them into
`scripts/promote-gates.sh`, and `references/promote-extensions.md` is the
forwarding address. The last section is different in kind — it describes a rule
`promote_cli.py` itself follows, and is here because that is where the reasoning
was written down.

## Origin identity, checked before any fetch

A repository-owned identity gate compares the live `git remote get-url origin`
against the internal remote it expects, before anything is fetched from the
public target. This is an identity check, not a convenience: it exists so that
running the promote script from the wrong checkout — a fork, a differently
named clone, a colleague's copy of the same project under a different path —
refuses immediately rather than silently publishing from the wrong source.

The comparison is always by full URL, never by remote name. Two distinct
GitLab projects in one namespace can both have a remote leaf named
`ai-skills.git`, differing only by an inserted path segment
(`skills/ai-skills.git` versus `ai-skills.git`, for example). A name-based
comparison cannot distinguish them; a URL-based one always can.

The base leaves this out because it asserts a fact a CI checkout already
establishes, and on a workstation it asserts the operator's remote naming
rather than anything about the tag being promoted. `.promote-target` carries no
key for it.

## Why ancestry cannot substitute for identity

A naive substitute for the identity check is: "is the tag reachable from, or
does it share history with, the public target?" This fails for exactly the
case that matters most: a fork that shares a real root commit with its
upstream reads as ahead-and-not-behind — the identical signature a
legitimately-behind public copy produces. Ancestry alone cannot tell a fork
from a copy that is merely lagging.

## The tip-parent ancestry test

Where ancestry is checked at all, it is checked narrowly: the merge base of
the candidate tag and the public branch tip must equal the public tip's
*direct parent*, not merely be *an ancestor of* it. "An ancestor of" would
pass for a public copy that is arbitrarily far behind, including one whose
entire history diverged from the internal line generations ago and only happens
to share an old commit. Requiring equality with the immediate parent means the
public tip is exactly one publish behind the tag being offered — the only state
a force-push amend-and-retag could safely resolve.

It is also the check most likely to fail closed on a truncated graph, which is
what trains operators to bypass a gate. **It can no longer match at all.** The
current `promote_cli.py` builds the public commit from the filtered tree with
`git commit-tree`, on a parent the target already holds, so the public line
shares no commit with the internal one and the merge base is empty. The base's
floor in its place is the lease: `promote_cli.py` pushes with `--force-with-lease`
expecting the tip it built on, and never falls back to a bare force, so a public
tip that moved after that fails the run instead of being overwritten. Which tip it
builds on depends on the clone — see `references/promote-extensions.md` §3.

## Tag objects without moving a ref

The public tag object is built with `git mktag` and pushed by SHA, never with
`git tag -f`. A worktree — which `assets/promote_cli.py` uses to build the
filtered tree without touching the operator's checkout — shares
`refs/tags` with its main repository. Forcing a tag ref inside a worktree moves
the *operator's own* tag of that name, not a separate "worktree tag."
`git mktag` writes an object into the store and writes no ref at all, so the
operator's clone is unaffected regardless of what the worktree does.

This one is not optional and not repository-owned: it is how the base creates
every public tag.
