#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = []
# ///
"""Promote one internal tag's filtered tree to a public target.

Invoked by its own path, which is not fixed — this script resolves the
repository root itself and may live anywhere inside it:

  uv run <this-script> [TAG]                             # dry run — reports, pushes nothing
  CONFIRM_SHA=<tag object id> uv run <this-script> TAG   # promotes

A dry run prints the exact confirming command for wherever it was invoked from,
so there is no path here to keep in sync.

TAG defaults to the newest strict-semver tag on origin. Three refusals, all
before the worktree exists: the configuration is absent, CONFIRM_SHA is not the
tag's object id, or PUBLISH_PATHS does not describe the tag's tree. That last one
has four forms — an absent path, an ancestor component that is a file, an entry
an ancestor entry already ships, and a malformed entry — and they are ONE
refusal, because they are four answers to one question. The tag must also exist
on origin as an annotated tag whose own name is TAG — a precondition, not a
policy, and what keeps a never-pushed bootstrap tag unpublishable. A confirmed run also needs the target
to be readable, because the public commit is built on the target's own tip.

NO INTERNAL HISTORY IS PUBLISHED. The public commit carries the filtered tree,
the publisher identity, and a message naming the tag, and its only parent is a
commit the target already holds, or none. See "the parent" below.

PUBLISH_PATHS ENTRIES MAY BE NESTED, at any depth, naming a directory or a file.
A directory no entry names but some entry reaches into is published PARTIALLY:
the named descendants ship and every unnamed sibling is withheld by the same
absence that withholds an unnamed top-level path. The allowlist property is not
weaker below the first level — which is why the report names what each descended
level left behind.

THIS IS A BASE. Every other check is the installing repository's policy and goes
in scripts/promote-gates.sh; references/promote-extensions.md gives the shape of
each one omitted here, and the reasoning behind the choices below. Nothing here
is a stub to fill in.

AN ABSENT CONFIRMATION IS THE DRY RUN, and there is no --dry-run flag: a flag
that can be passed makes the confirmation unreachable. CONFIRM_SHA is read from
the ENVIRONMENT only and .promote-target is PARSED, never sourced, so neither it
nor the gate hook can authorize a push.

THE CONFIRMATION IS THE TAG OBJECT'S ID, not its name and not its commit's. A tag
object holds its name, its commit, and its annotation, so the id changes when any
of them does: a tag re-pointed after the dry run, or re-cut with a rewritten
annotation, refuses. The commit's id would miss the second — and the annotation
is published, as the public tag's message. The tag is resolved to that id once,
and every later read is of the id, never of refs/tags/TAG again.
"""

import os
import re
import shutil
import signal
import subprocess  # nosec B404 # runs git and fixed commands, never a shell
import sys
import tempfile
from pathlib import Path

USAGE = "usage: promote_cli.py [TAG]"
PUBLIC_BRANCH = "main"
PUBLIC_REMOTE = "promote-public"  # left configured deliberately — see the push


def err(*lines: str) -> None:
    for line in lines:
        print(line, file=sys.stderr)


def die(message: str, *hints: str):
    err(f"error: {message}", *(f"hint: {hint}" for hint in hints))
    sys.exit(1)


def git(*args: str, quiet: bool = False, **kwargs) -> subprocess.CompletedProcess:
    """`git <args>`, stdout captured, status left to the caller. A list, never a
    shell. `quiet` discards stderr where the bash version sent it to /dev/null."""
    return subprocess.run(  # nosec B603 B607 # argument list; git found on PATH
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL if quiet else None,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
        **kwargs,
    )


def output(*args: str, **kwargs) -> str:
    """A command substitution under `set -e`: stdout without its trailing
    newlines, or this script exits with git's own status."""
    result = git(*args, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)
    return result.stdout.rstrip("\n")


def call(*args: str, **kwargs) -> None:
    """A bare git command under `set -e`."""
    status = subprocess.run(["git", *args], check=False, **kwargs).returncode  # nosec B603 B607 # argument list; git found on PATH
    if status != 0:
        sys.exit(status)


def malformed_reason(want: str) -> str:
    """Why an entry's SHAPE is not a path, or "" — the first matching form wins."""
    parts = want.split("/")
    if want == "":
        return "an empty entry"
    if want.startswith("/"):
        return "a leading separator"
    if want.endswith("/"):
        return "a trailing separator"
    if "//" in want:
        return "an empty component"
    if ".." in parts:
        return "a .. component"
    if "." in parts:
        return "a . component"
    return ""


def newest_semver_tag() -> str:
    """The newest strict-semver tag on origin, by version — a string sort ranks
    v0.1.2 above v0.1.10."""
    tags = []
    for line in git("ls-remote", "--tags", "--refs", "origin", quiet=True).stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2:
            name = fields[1].removeprefix("refs/tags/")
            match = re.fullmatch(r"v([0-9]+)\.([0-9]+)\.([0-9]+)", name)
            if match:
                tags.append((tuple(int(n) for n in match.groups()), name))
    return max(tags)[1] if tags else ""


def promote(argv: list, cleanup: list) -> int:
    # No prompt may block a job or wait on a terminal.
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
    repo_root = output("rev-parse", "--show-toplevel")
    # Derived, never hardcoded: the only command this script prints for an
    # operator to copy is the one that promotes, and a wrong path there is the one
    # papercut guaranteed to be hit. Installed at scripts/promote_cli.py this
    # reports `scripts/promote_cli.py`; moved anywhere else inside the repository
    # it reports where it actually is.
    #
    # BOTH SIDES ARE RESOLVED, and that is why the root is resolved a second time
    # here rather than used as git printed it. On a tree reached through a
    # symlinked ancestor a logical and a physical path disagree and the prefix
    # fails to match. macOS makes this the common case, not the exotic one: /tmp
    # and /var are symlinks to /private/tmp and /private/var, so every run under
    # a temporary directory hits it.
    #
    # If the path is still not under the root it stays absolute: a correct
    # runnable command, merely a verbose one, so there is no failure path here.
    self_path = Path(__file__).resolve()
    try:
        self_rel = str(self_path.relative_to(Path(repo_root).resolve()))
    except ValueError:
        self_rel = str(self_path)
    os.chdir(repo_root)
    config_file = f"{repo_root}/.promote-target"
    gate_hook = Path(repo_root) / "scripts" / "promote-gates.sh"

    # --- refusal 1: configuration absent -----------------------------------
    if not Path(config_file).is_file():
        die(
            f"no promote configuration at {config_file}",
            "copy assets/promote-target.template there and fill in all three keys",
        )
    # A value is LITERAL — quotes are part of it, so PUBLISH_PATHS="skills" names
    # a path including the quotes and refusal 2 says so. One line per path:
    # newline is the only separator a path cannot hold.
    config = {"PUBLIC_TARGET": "", "PUBLISHER_IDENTITY": ""}
    publish_paths = []
    for line in Path(config_file).read_bytes().decode("utf-8", "surrogateescape").split("\n"):
        if line == "" or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key in config:
            config[key] = value
        elif key == "PUBLISH_PATHS":
            publish_paths.append(value)
        elif key in ("CONFIRM_SHA", "DRY_RUN"):
            err(
                f"note: {key} here is ignored — the confirmation is read from the",
                "      environment only, so this file cannot authorize a push",
            )
    for key, value in config.items():
        if not value:
            die(f"{config_file} declares no {key}")
    if not publish_paths:
        die(f"{config_file} declares no PUBLISH_PATHS")
    public_target, publisher_identity = config["PUBLIC_TARGET"], config["PUBLISHER_IDENTITY"]

    # --- refusal 2, first form: an entry whose SHAPE is not a path ---------
    # A shape fault needs no tree to see, so it is caught here rather than
    # against the tag. That is observable, not tidiness: the same refusal then
    # arrives whether the tag was named or derived, and a repository with no tag
    # at all still gets the real reason instead of "origin carries no
    # strict-semver tag".
    #
    # An entry names a path relative to the repository root. A leading separator
    # would read as absolute, a trailing one or an empty component as a typo, and
    # '.' or '..' as a traversal an allowlist has no business expressing. One
    # reason per entry: the first matching form is the one reported.
    malformed = [f"'{want}' — {reason}" for want in publish_paths if (reason := malformed_reason(want))]
    if malformed:
        err(f"error: {config_file} names {len(malformed)} unusable PUBLISH_PATHS entry(s):")
        err(*(f"  {line}" for line in malformed))
        err(
            "hint: an entry names a path relative to the repository root, at any depth —",
            "      no leading or trailing separator, no empty component, and no '.' or",
            "      '..' component. A fault in an entry's shape needs no tree to see, so",
            "      it refuses before any tag is resolved.",
        )
        sys.exit(1)

    # --- the tag -----------------------------------------------------------
    tag = argv[0] if argv else ""
    if tag.startswith("-"):
        die(
            f"unknown flag: {tag} — this script takes no flags",
            "omitting CONFIRM_SHA is what makes a run a dry run",
        )
    if not tag:
        tag = newest_semver_tag()
        if not tag:
            die("origin carries no strict-semver tag")
    # Absent from origin is not an internal release; lightweight has no annotation.
    if not git("ls-remote", "--tags", "--refs", "origin", f"refs/tags/{tag}", quiet=True).stdout:
        die(
            f"{tag} is not a tag on origin",
            "a local-only tag — a bootstrap tag, say — is not an internal release",
        )
    if git("cat-file", "-t", f"refs/tags/{tag}", quiet=True).stdout.strip() != "tag":
        die(
            f"{tag} is not an annotated tag in this clone",
            "git fetch origin --tags — the promotion reuses the annotation",
        )
    # THE ONE READ OF refs/tags/<tag>. Everything below reads the object id, so a
    # ref that moves during the run — under a gate hook, say — changes nothing
    # that is pushed. The raw object is read here too, for its name, its tagger
    # date and its annotation.
    tag_id = output("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")
    commit_id = output("rev-parse", "--verify", "--quiet", f"{tag_id}^{{commit}}")
    raw = git("cat-file", "tag", tag_id).stdout
    header, _, annotation = raw.partition("\n\n")
    fields = dict(line.split(" ", 1) for line in header.split("\n") if " " in line)
    # A ref can name a tag object cut under another name. The confirmation binds
    # the object's own name, so it has to be the name being promoted.
    if fields.get("tag") != tag:
        die(
            f"refs/tags/{tag} points at a tag object named '{fields.get('tag', '')}'",
            "a tag ref copied under a new name is not a release of that name",
        )

    # --- refusal 2, remaining forms: the allowlist vs the tag's tree -------
    # A count of entries is no substitute for any of this: it passes against an
    # entry naming a path that does not exist, which is the case that ships a
    # wrong tree.
    #
    # `git rev-parse --verify --quiet "<tag>:<path>"` is the existence test.
    # Listing the tree cannot be: it exits 0 with EMPTY OUTPUT for an absent path
    # (measured). rev-parse also interprets no glob character, so 'we[i]rd/sub'
    # resolves as written and needs none of the ':(literal)' care a pathspec does.
    faults = []
    for want in publish_paths:
        # An entry an ancestor entry already ships whole is dead configuration
        # that reads as a narrowing in effect. It REFUSES rather than warns: a
        # warning lands in a report nobody rereads, and deleting the ancestor
        # line later — reasonably, believing the specific line governs — would
        # then narrow what ships silently.
        shadow = next(
            (other for other in publish_paths if other != want and want.startswith(f"{other}/")), ""
        )
        if shadow:
            faults.append(f"'{want}' — '{shadow}' already ships it")
            continue
        # Every STRICT ancestor component must be a tree, checked shallowest
        # first and BEFORE the entry itself, so the message names the component
        # that cannot be descended into rather than reporting a correctly-spelled
        # path as a typo.
        fault = ""
        components = want.split("/")
        for depth in range(1, len(components)):
            prefix = "/".join(components[:depth])
            kind = git("cat-file", "-t", f"{tag_id}:{prefix}", quiet=True).stdout.strip()
            if not kind:
                fault = "no such path at the tag"
                break
            if kind != "tree":
                fault = f"'{prefix}' is not a directory"
                break
        if not fault and git(
            "rev-parse", "--verify", "--quiet", f"{tag_id}:{want}", quiet=True
        ).returncode != 0:
            fault = "no such path at the tag"
        if fault:
            faults.append(f"'{want}' — {fault}")
    if faults:
        err(f"error: {config_file} names {len(faults)} PUBLISH_PATHS entry(s) the tree at {tag} does not describe:")
        err(*(f"  {line}" for line in faults))
        err(
            "hint: a misspelling, a path that has moved, or two entries merged onto one",
            "      line. If it is deliberately gone, delete its PUBLISH_PATHS line — the",
            "      allowlist names what ships, so that withholds nothing. If an ancestor",
            "      entry already ships it, the narrowing the entry implies is not in",
            "      effect: delete one of the two lines, whichever states what you mean.",
        )
        sys.exit(1)

    # --- the traversal: ONE descent feeds both the report and the push -----
    # Per child of every visited directory, EXACTLY ONE of three things: a child
    # that is an allowlist entry is kept whole and not descended into, a child
    # some entry reaches into is descended into, and anything else is removed.
    # Total and mutually exclusive, which is what makes the result auditable —
    # every child of every visited directory lands in exactly one bucket.
    #
    # IT READS THE TAG'S TREE AND NEVER A WORKTREE, because the dry run exits
    # before one exists. That constraint buys the design's best property: the
    # report and the push come from one computation, so the removal loop further
    # down is the execution of a decision already made and already printed,
    # rather than a second place the decision gets made.
    #
    # The record form is the PORTABLE one — `<mode> SP <type> SP <oid> TAB
    # <name>`, NUL-terminated under -z, so a name holding a space or a newline is
    # read as written. Asking git to format the listing needs git >= 2.36, and
    # this file is installed into repositories whose git version it cannot see.
    # `<tree-ish>:<path>` is what makes the descent safe — it resolves a path
    # literally, with no pathspec globbing, so 'we[i]rd' descends correctly.
    entries = set(publish_paths)
    queue = [""]  # "" is the root tree; every other entry is a directory path
    kept = []  # what ships, in tree order
    remove = []  # what is removed, each named at the shallowest level it can be
    report = []  # the per-level withheld blocks, in the order descended
    for directory in queue:
        level = []
        children = 0
        listing = git("ls-tree", "-z", f"{tag_id}:{directory}").stdout
        for record in filter(None, listing.split("\0")):
            children += 1
            meta, _, name = record.partition("\t")
            kind = meta.split(" ")[1]
            path = f"{directory}/{name}" if directory else name
            if path in entries:
                kept.append(path)
            elif any(entry.startswith(f"{path}/") for entry in publish_paths):
                # Only a tree can be descended into, and entry validation above
                # already proved every ancestor component of every entry is one.
                # So this is an assertion that the two agree, not a policy:
                # reaching it would mean the traversal was about to remove a path
                # the allowlist publishes.
                if kind != "tree":
                    die(f"internal: {path} is a {kind}, but the allowlist names something beneath it")
                queue.append(path)
            else:
                remove.append(path)
                level.append(path)
        if not directory and children == 0:
            die(f"the tree at {tag} has no top-level entries")
        # A level contributes a withheld block only when it left something behind.
        # A directory shipped whole is never visited, so it is never expanded.
        if level:
            report.append(f"withheld under {directory}:" if directory else "withheld:")
            report.extend(f"  {path}" for path in level)
    # Every entry is reached exactly once: validation proved each one resolves at
    # the tag, and the descent visits every strict ancestor of every entry. A
    # mismatch means validation and traversal disagree about the tree, which
    # would publish or withhold something nobody named. An invariant, not a
    # refusal — it encodes no policy and there is no configuration that reaches
    # it.
    #
    # DISTINCT entries, not raw lines. A duplicated PUBLISH_PATHS line is dead but
    # harmless: it names exactly what already ships, so it is none of the four
    # ways an allowlist fails to describe the tree, and it must promote.
    if len(kept) != len(entries):
        die(f"internal: the traversal kept {len(kept)} of {len(entries)} declared path(s)")
    if gate_hook.exists() and os.access(gate_hook, os.X_OK):
        hook_state = "present"
    elif gate_hook.exists():
        hook_state = "PRESENT BUT NOT EXECUTABLE — it will NOT run (chmod +x it, or remove it)"
    else:
        hook_state = "not present"

    # --- the parent: what the public commit is built on --------------------
    # Decided here, before the report, and printed with it, so the dry run and
    # the push read one answer. Three sources, in order:
    #
    #   1. a remote-tracking ref for the target — the record of what THIS CLONE
    #      last promoted. Only a push to the named remote writes it; nothing here
    #      fetches into it. The lease stays bare and expects exactly that record.
    #   2. the target's current tip, when the clone holds no record — ADOPTED as
    #      the parent, with a lease naming exactly that tip. This is what the
    #      first promotion to a target holding an initial commit needs; a bare
    #      lease with no record expects no branch at all and is refused with
    #      `stale info`.
    #   3. no branch on the target — a root commit, and a bare lease expecting
    #      none.
    #
    # A FRESH CLONE HAS NO RECORD, SO EVERY CI RUN TAKES SOURCE 2. There the lease
    # guards only the interval between this read and the push: a commit someone
    # else put on the target becomes the parent rather than a refusal, and the
    # promoted tree replaces its content. The dry run names it. A repository that
    # wants that refused adds the divergence gate in
    # references/promote-extensions.md.
    #
    # READ-ONLY ON EVERY PATH, because the dry run exits after the report: a
    # local ref, or ls-remote against the URL, which configures no remote and
    # fetches nothing. An unreadable target — a private one, read by a job
    # holding no credential, which is every CI dry run — is reported here, and
    # only a confirmed run fails on it.
    parent = ""
    adopt = False
    unreadable = False
    lease = "--force-with-lease"
    remote_url = git("remote", "get-url", PUBLIC_REMOTE, quiet=True).stdout.rstrip("\n")
    record = git(
        "rev-parse", "--verify", "--quiet", f"refs/remotes/{PUBLIC_REMOTE}/{PUBLIC_BRANCH}^{{commit}}"
    ) if remote_url == public_target else None
    tip = None
    if record is not None and record.returncode == 0:
        parent = record.stdout.rstrip("\n")
        parent_report = f"{parent} — the commit this clone last promoted"
    elif (tip := git("ls-remote", public_target, f"refs/heads/{PUBLIC_BRANCH}", quiet=True)).returncode == 0:
        # ls-remote matches a pattern against the END of each ref name; compare
        # exactly.
        parent = next(
            (
                fields[0]
                for fields in (line.split() for line in tip.stdout.splitlines())
                if len(fields) >= 2 and fields[1] == f"refs/heads/{PUBLIC_BRANCH}"
            ),
            "",
        )
        if parent:
            adopt = True
            lease = f"--force-with-lease=refs/heads/{PUBLIC_BRANCH}:{parent}"
            parent_report = (
                f"{parent} — the target's current tip, adopted: this clone holds no record of a promotion to it"
            )
        else:
            parent_report = (
                f"none — the target has no {PUBLIC_BRANCH} branch, so the public commit is a root commit"
            )
    else:
        unreadable = True
        parent_report = "unknown — the target could not be read (a private target cannot be read without a credential)"

    # --- the report, printed on every run ----------------------------------
    print(f"tag:        {tag}")
    print(f"tag object: {tag_id} — the id CONFIRM_SHA must equal")
    print(f"commit:     {commit_id} — what the tag points at, which is not the confirmation")
    print(f"target:     {public_target}")
    print(f"parent:     {parent_report}")
    print("history:    not published — the public commit carries the filtered tree and no internal commit")
    # Both halves come from the traversal, not from the configuration, so the
    # report describes the tree that is about to be pushed rather than the list
    # that was declared. A PARTIALLY PUBLISHED DIRECTORY IS WHERE THIS
    # ALLOWLIST'S ACCEPTED FAILURE MODE HIDES: a new page added beside the
    # published ones silently does not ship. The per-level block is what keeps
    # that failure quiet rather than silent — a builder who forgot an allowlist
    # line reads it here, on the next dry run, instead of discovering it as a
    # missing page in the public tree.
    print("ships:")
    for path in kept:
        print(f"  {path}")
    if report:
        for line in report:
            print(line)
    else:
        print(f"withheld:   nothing — the allowlist names every path in the tree at {tag}")
    print(f"repo gates: {hook_state}")

    # --- refusal 3: the confirmation must equal the tag object's id ---------
    # Exact, full-length equality. The three near misses each get their own
    # sentence, because each is a different mistake: the name is what this
    # confirmation used to be, the commit id is what a merge request page shows,
    # and a prefix is a truncated paste.
    confirm = os.environ.get("CONFIRM_SHA", "")
    if not confirm:
        if os.environ.get("CONFIRM_TAG", ""):
            err("warning: CONFIRM_TAG is retired and ignored — CONFIRM_SHA, the tag object id, replaces it")
        print("dry run: nothing was pushed.")
        print(f"to promote: CONFIRM_SHA={tag_id} uv run {self_rel} {tag}")
        return 0
    if confirm != tag_id:
        if confirm == commit_id:
            die(
                f"CONFIRM_SHA is {tag}'s commit id, not its tag object id",
                f"the tag object id covers the annotation too: CONFIRM_SHA={tag_id}",
            )
        if confirm == tag:
            die(
                "CONFIRM_SHA is the tag's name, not its object id",
                f"the confirmation is the tag object id: CONFIRM_SHA={tag_id}",
            )
        if tag_id.startswith(confirm):
            die(
                f"CONFIRM_SHA '{confirm}' is an abbreviated id",
                f"the confirmation is the full tag object id: CONFIRM_SHA={tag_id}",
            )
        die(
            f"CONFIRM_SHA is '{confirm}' but the tag object being promoted, {tag}, is {tag_id}",
            "a prepared command whose tag moved under it fails closed here",
        )
    # A precondition, like the tag being on origin, and not a fourth refusal:
    # with no readable target there is nothing to build on, and the push would
    # fail the same way, only later.
    if unreadable:
        die(
            f"cannot read {public_target} — nothing pushed",
            "a private target needs a credential wherever the confirmed promotion runs",
        )
    # Executed, never sourced: a child process, TAG and PUBLIC_TARGET exported
    # beside the inherited CONFIRM_SHA, exit status only — it cannot set the confirmation or cause a push. Absent is
    # not an error.
    if hook_state == "present":
        hook = subprocess.run(  # nosec B603 # the repository's own gate hook, executed by path
            [str(gate_hook)], env={**os.environ, "TAG": tag, "PUBLIC_TARGET": public_target}
        )
        if hook.returncode != 0:
            die("scripts/promote-gates.sh refused the promotion — nothing pushed")
    elif gate_hook.exists():
        err(f"warning: {gate_hook} is not executable and did not run")

    # --- filter, commit, retag, push ---------------------------------------
    # The worktree lives in a directory mkdtemp creates, and the `finally` in
    # main() removes both the worktree and that directory on every exit.
    # --force, because the worktree ends with staged removals and a plain remove
    # refuses a worktree with changes.
    scratch = tempfile.mkdtemp(prefix="promote.")
    worktree_dir = f"{scratch}/promote"
    cleanup.append(lambda: shutil.rmtree(scratch, ignore_errors=True))
    cleanup.append(
        lambda: Path(worktree_dir).is_dir()
        and git("worktree", "remove", "--force", worktree_dir, quiet=True)
    )
    call("worktree", "add", "--quiet", "--detach", worktree_dir, commit_id)
    # ':(literal)' is load-bearing: git reads a pathspec as a glob, so a name
    # holding '[', '*', or '?' would match something else, or nothing, and be
    # silently kept.
    #
    # REMOVALS STAY SHALLOW. The traversal names a withheld path at the shallowest
    # level it can, so this loop's invocation count follows the tree's shape
    # rather than its file count. A directory this loop descends past is never
    # emptied by it: the traversal descends into a directory only because some
    # entry ships beneath it.
    for path in remove:
        call("-C", worktree_dir, "rm", "-rq", "--", f":(literal){path}")
    # An adopted tip is fetched only now, because commit-tree needs the parent
    # object. By id, so the commit built on is the one the report named and the
    # lease expects; and into no ref, so the record above stays something only a
    # push writes.
    if adopt:
        call("fetch", "--quiet", "--no-tags", public_target, parent)
    # commit-tree, NOT commit --amend. An amended commit keeps its parents, so its
    # push sent every earlier internal commit too: each withheld path at each past
    # revision, each internal subject, each author address. commit-tree writes one
    # object from the filtered tree and moves no ref, the property mktag gives the
    # tag below.
    #
    # Identity from the environment, which outranks both git config and an
    # inherited GIT_AUTHOR_*. Both dates are the tag's tagger date, so one tag
    # promoted onto one parent always builds the same commit. The message names
    # the tag and nothing else; the notes stay in the annotation. commit-tree runs
    # no hooks, and gpgsign=false keeps a configured signing key from failing a
    # publish at its latest possible moment.
    tree = output("-C", worktree_dir, "write-tree")
    # `<seconds> <offset>`, the tail of the tagger line after the address — what
    # `%(taggerdate:raw)` prints, read from the object rather than the ref.
    tagger_date = fields.get("tagger", "").rpartition("> ")[2]
    identity = {
        "GIT_AUTHOR_NAME": "promote",
        "GIT_AUTHOR_EMAIL": publisher_identity,
        "GIT_AUTHOR_DATE": tagger_date,
        "GIT_COMMITTER_NAME": "promote",
        "GIT_COMMITTER_EMAIL": publisher_identity,
        "GIT_COMMITTER_DATE": tagger_date,
    }
    public_commit = output(
        "-c", "commit.gpgsign=false", "commit-tree", tree, *(["-p", parent] if parent else []),
        "-m", f"Promote {tag}",
        env={**os.environ, **identity},
    )
    # The annotation is reused as the bash version reused it: its trailing
    # newlines reduced to one, nothing asserted about its content, so a hand-cut
    # tag promotes. git mktag writes an object and no ref: a worktree shares
    # refs/tags with its parent, so `git tag -f` would move the OPERATOR's tag.
    tag_object = output(
        "mktag",
        input=(
            f"object {public_commit}\n"
            "type commit\n"
            f"tag {tag}\n"
            f"tagger promote <{publisher_identity}> {tagger_date}\n"
            "\n"
            f"{annotation.rstrip(chr(10))}\n"
        ),
    )
    # A configured remote, LEFT in place: the push writes its remote-tracking ref,
    # and that ref is the record "the parent" reads first on the next run from
    # this clone. The lease expects the tip the public commit was built on — the
    # record, the adopted tip, or no branch — so any other public tip refuses the
    # push rather than being overwritten. That is the base's floor in place of a
    # divergence gate.
    if remote_url != public_target:
        git("remote", "remove", PUBLIC_REMOTE, quiet=True)
        call("remote", "add", PUBLIC_REMOTE, public_target)
    # --atomic: branch and tag land together or neither does. No fallback.
    call(
        "push", "--quiet", "--atomic", lease, PUBLIC_REMOTE,
        f"{public_commit}:refs/heads/{PUBLIC_BRANCH}", f"{tag_object}:refs/tags/{tag}",
    )
    print(f"promoted {tag} to {public_target} ({len(kept)} path(s))")
    return 0


def main(argv: list) -> int:
    if argv[:1] in (["--help"], ["-h"]):
        print(USAGE)
        print()
        print(__doc__.split("\n\n", 1)[0])
        return 0
    cleanup = []
    try:
        return promote(argv, cleanup)
    finally:
        # Worktree first, then the directory that held it.
        for step in reversed(cleanup):
            step()


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="surrogateescape", line_buffering=True)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    sys.exit(main(sys.argv[1:]))
