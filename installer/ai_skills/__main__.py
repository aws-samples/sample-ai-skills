"""`ai-skills`: the TUI, or the same install from flags.

Every choice the TUI offers has a flag. With `--yes` and every choice given, the
install runs without drawing a screen and prints what it wrote. Without `--yes`,
the TUI starts with whatever the flags chose already selected, and with every
skill selected when no `--skill` flag is given.

Exit status: 0 when every requested skill was written or removed; 1 when one
was not (a conflict, a failed write, an uninstall left in place) or the catalog
could not be read; 2 for a usage error, which writes nothing.
"""

import argparse
import os
import sys
from pathlib import Path

from . import __version__, agents, catalog, install, plan

AGENT_IDS = [agent.id for agent in agents.AGENTS]

#: The skill whose install ends with a next-step line (spec: installer/next-step-hint).
#: It records facts about one repository, so it does nothing until it is run in each.
SETUP_SKILL = "ai-scaffold-dev-context"
NEXT_STEP = f"Next: run /{SETUP_SKILL} in each repository you work in, to record how it is developed."


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(
        prog="ai-skills",
        description="Install this repository's skills into a coding agent's skills directory.",
        epilog="Run with no arguments to choose in the interactive installer.",
    )
    top.add_argument("--version", action="version", version=f"ai-skills {__version__}")
    top.add_argument("--agent", action="append", choices=AGENT_IDS, metavar="AGENT",
                     help=f"install for this agent; repeatable. One of: {', '.join(AGENT_IDS)}")
    top.add_argument("--skill", action="append", metavar="SKILL", help="install this skill; repeatable")
    top.add_argument("--all", action="store_true", help="install every skill in the catalog")
    top.add_argument("--scope", choices=plan.SCOPES,
                     help="user: the agent's directory in your home; project: the current git repository")
    top.add_argument("--yes", action="store_true", help="install without the interactive installer")
    top.add_argument("--overwrite", action="store_true", help="with --yes, replace skill directories that already exist")

    commands = top.add_subparsers(dest="command", metavar="{list,uninstall}")
    commands.add_parser("list", help="show what this installer recorded, per agent and scope")
    remove = commands.add_parser("uninstall", help="remove skills this installer recorded")
    remove.add_argument("--agent", action="append", choices=AGENT_IDS, metavar="AGENT", required=True,
                        help=f"repeatable. One of: {', '.join(AGENT_IDS)}")
    remove.add_argument("--scope", choices=plan.SCOPES, required=True)
    remove.add_argument("--skill", action="append", metavar="SKILL", help="repeatable")
    remove.add_argument("--all", action="store_true", help="every skill recorded for that agent and scope")
    return top


def usage_error(message: str) -> int:
    print(f"ai-skills: {message}", file=sys.stderr)
    return 2


def selected_skills(found: catalog.Catalog, args) -> list | None:
    """The skills the flags name, in catalog order, or None after reporting an
    unknown name."""
    if args.all:
        return list(found.names)
    names = args.skill or []
    unknown = [name for name in names if name not in found.names]
    if unknown:
        usage_error(f"unknown skill {', '.join(unknown)}; valid skills: {', '.join(found.names)}")
        return None
    return [name for name in found.names if name in names]


def run_install(args, *, cwd: Path, home: Path, env) -> int:
    found = catalog.load()
    skills = selected_skills(found, args)
    if skills is None:
        return 2
    agent_ids = [i for i in AGENT_IDS if i in (args.agent or [])]

    if not args.yes:
        if args.overwrite:
            return usage_error("--overwrite applies only with --yes; the interactive installer asks instead")
        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            return usage_error(
                "no terminal to draw the installer on; pass --agent, --skill or --all, --scope and --yes"
                " to install without it"
            )
        from .tui import InstallerApp, Selection

        # With no --skill flag, every skill starts selected.
        app = InstallerApp(
            found, version=__version__, cwd=cwd, home=home, env=env,
            selection=Selection(agents=agent_ids, skills=skills or list(found.names), scope=args.scope or "user"),
        )
        outcomes = app.run()
        if outcomes is None:
            print("Nothing was installed.")
            return 0
        if isinstance(outcomes, install.ManifestError):
            # The result screen already showed it; main() prints it to stderr
            # and returns 1, exactly as it does without the interface.
            raise outcomes
        return report(outcomes)

    missing = [flag for flag, given in (("--agent", agent_ids), ("--skill or --all", skills), ("--scope", args.scope)) if not given]
    if missing:
        return usage_error(f"--yes needs {', '.join(missing)}")
    built = plan.build(found, agent_ids, skills, args.scope, cwd=cwd, home=home, env=env)
    print(plan.render(built), end="")
    print()
    return report(install.execute(built, version=__version__, overwrite=args.overwrite))


def report(outcomes: list) -> int:
    for outcome in outcomes:
        print(outcome)
    if any(o.status == "written" and o.write.skill.name == SETUP_SKILL for o in outcomes):
        print(NEXT_STEP)
    return 0 if all(o.status == "written" for o in outcomes) else 1


def run_list(*, cwd: Path, home: Path, env) -> int:
    found = install.listings(home=home, project=plan.project_dir(cwd), env=env)
    if not found:
        print("No installs recorded.")
        return 0
    for listing in found:
        print(f"{listing.agent.label}, {listing.scope} scope: {plan.shown(listing.directory)}")
        for entry, present in listing.entries:
            state = f"installed {entry.get('installed_at', '')}" if present else "recorded but missing"
            print(f"  {entry['skill']}  {entry.get('version', '')}  {state}")
    return 0


def run_uninstall(args, *, cwd: Path, home: Path, env) -> int:
    if bool(args.skill) == args.all:
        return usage_error("uninstall needs exactly one of --skill or --all")
    project = plan.project_dir(cwd)
    ok = True
    for agent_id in dict.fromkeys(args.agent):
        directory = agents.get(agent_id).directory(args.scope, home=home, project=project, env=env)
        names = [e["skill"] for e in install.read_manifest(directory)] if args.all else args.skill
        for _, removed, message in install.uninstall(directory, names):
            print(message)
            ok = ok and removed
    return 0 if ok else 1


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    cwd, home, env = Path.cwd(), Path.home(), os.environ
    try:
        if args.command == "list":
            return run_list(cwd=cwd, home=home, env=env)
        if args.command == "uninstall":
            return run_uninstall(args, cwd=cwd, home=home, env=env)
        return run_install(args, cwd=cwd, home=home, env=env)
    except (catalog.CatalogError, install.ManifestError) as error:
        print(f"ai-skills: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
