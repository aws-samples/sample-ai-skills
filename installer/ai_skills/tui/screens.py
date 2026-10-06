"""One Screen per step, the conflict modal the confirmation screen opens, and the
result screen the install ends on."""

import os

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.content import Content
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, RadioSet, SelectionList, Static

from .. import agents, install, plan
from .banner import Banner
from .widgets import CheckList, ScopeOption


def buttons(*items: Button) -> Horizontal:
    return Horizontal(*items, classes="buttons")


class Step(Screen):
    BINDINGS = [("escape", "back", "Back"), ("ctrl+q", "app.quit", "Quit")]

    def action_back(self) -> None:
        self.save()
        if len(self.app.screen_stack) > 2:
            self.app.pop_screen()

    def save(self) -> None:
        """Copy this screen's choice onto the App's selection."""

    @on(Button.Pressed, "#back")
    def back_pressed(self) -> None:
        self.action_back()

    @on(Button.Pressed, "#quit")
    def quit_pressed(self) -> None:
        # None before the install has run, so Quit here still reports that
        # nothing was installed; the same expression on the result screen
        # returns the outcomes.
        self.app.exit(self.app.result)


class AgentsScreen(Step):
    # The first screen has nothing to go back to.
    BINDINGS = [Binding("escape", "back", "Back", show=False)]

    def compose(self) -> ComposeResult:
        yield Banner(id="banner")
        yield Static(f"[$secondary]version {self.app.version}[/]", id="version")
        yield Static("Which agents should the skills be installed for?", classes="prompt")
        chosen = set(self.app.selection.agents)
        yield CheckList(*[(a.label, a.id, a.id in chosen) for a in agents.AGENTS], id="agents")
        yield buttons(Button("Quit", id="quit"), Button("Next", id="next", variant="primary"))
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#agents").border_title = "Agents"

    def on_screen_suspend(self) -> None:
        self.query_one(Banner).pause()

    def on_screen_resume(self) -> None:
        self.query_one(Banner).resume()

    def save(self) -> None:
        self.app.selection.agents = list(self.query_one("#agents", SelectionList).selected)

    @on(Button.Pressed, "#next")
    def next_pressed(self) -> None:
        self.save()
        if not self.app.selection.agents:
            self.notify("Select at least one agent.", severity="warning")
            return
        self.app.push_screen(SkillsScreen())


class SkillsScreen(Step):
    def compose(self) -> ComposeResult:
        yield Static("Which skills? Space selects; the highlighted skill is described on the right.", classes="prompt")
        chosen = set(self.app.selection.skills)
        with Horizontal(id="skills-row"):
            with VerticalScroll(id="skills"):
                for domain, skills in self.app.catalog.by_domain().items():
                    yield Static(domain, classes="domain")
                    yield CheckList(
                        *[(s.name, s.name, s.name in chosen) for s in skills], id=f"domain-{domain}"
                    )
            yield Static("", id="description")
        yield buttons(
            Button("Back", id="back"), Button("Select all", id="all"), Button("Next", id="next", variant="primary")
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#skills").border_title = "Skills"
        first = self.app.catalog.skills[0]
        self.describe(first.name)

    def describe(self, name: str) -> None:
        skill = self.app.catalog.get(name)
        files = len(skill.files)
        description = self.query_one("#description", Static)
        description.border_title = skill.name
        description.update(
            f"{skill.name}  ({skill.domain})\n\n{skill.description}\n\n{files} file{'s' if files != 1 else ''}"
        )

    # Every list highlights its first option when it mounts, so only the focused
    # list's highlight is described; moving focus describes the new list's.
    @on(SelectionList.SelectionHighlighted)
    def highlighted(self, event: SelectionList.SelectionHighlighted) -> None:
        if event.selection_list.has_focus:
            self.describe(event.selection.value)

    def on_descendant_focus(self, event) -> None:
        if isinstance(event.widget, SelectionList) and event.widget.highlighted is not None:
            self.describe(event.widget.get_option_at_index(event.widget.highlighted).value)

    def save(self) -> None:
        chosen = {value for sl in self.query(SelectionList) for value in sl.selected}
        self.app.selection.skills = [name for name in self.app.catalog.names if name in chosen]

    @on(Button.Pressed, "#all")
    def all_pressed(self) -> None:
        for selection_list in self.query(SelectionList):
            selection_list.select_all()

    @on(Button.Pressed, "#next")
    def next_pressed(self) -> None:
        self.save()
        if not self.app.selection.skills:
            self.notify("Select at least one skill.", severity="warning")
            return
        self.app.push_screen(ScopeScreen())


class ScopeScreen(Step):
    def compose(self) -> ComposeResult:
        app = self.app
        project = plan.project_dir(app.cwd)
        selected = [agents.get(i) for i in app.selection.agents]

        def where(scope):
            return "\n".join(
                f"    {a.label}: {plan.shown(a.directory(scope, home=app.home, project=project, env=app.env))}" for a in selected
            )

        yield Static("Where should they be installed?", classes="prompt")
        with RadioSet(id="scope"):
            yield ScopeOption("User — available in every project", value=app.selection.scope == "user", id="user")
            yield ScopeOption(f"Project — {plan.shown(project)}", value=app.selection.scope == "project", id="project")
        yield Static(f"\nUser scope writes to:\n{where('user')}\n\nProject scope writes to:\n{where('project')}")
        yield buttons(Button("Back", id="back"), Button("Next", id="next", variant="primary"))
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#scope").border_title = "Scope"

    def save(self) -> None:
        pressed = self.query_one("#scope", RadioSet).pressed_button
        if pressed is not None:
            self.app.selection.scope = pressed.id

    @on(Button.Pressed, "#next")
    def next_pressed(self) -> None:
        self.save()
        app = self.app
        built = plan.build(
            app.catalog, app.selection.agents, app.selection.skills, app.selection.scope,
            cwd=app.cwd, home=app.home, env=app.env,
        )
        app.push_screen(ConfirmScreen(built))


class ConfirmScreen(Step):
    def __init__(self, built):
        super().__init__()
        self.plan = built

    def compose(self) -> ComposeResult:
        conflicts = len(self.plan.conflicts)
        note = ""
        if conflicts == 1:
            note = " 1 target already exists; you will be asked about it."
        elif conflicts:
            note = f" {conflicts} targets already exist; you will be asked about each."
        yield Static(f"This is what will be written. Nothing has been written yet.{note}", classes="prompt")
        with VerticalScroll(id="plan"):
            yield Static(plan.render(self.plan), markup=False)
        yield buttons(Button("Back", id="back"), Button("Install", id="install", variant="primary"))
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#plan").border_title = "Plan"

    @on(Button.Pressed, "#install")
    def install_pressed(self) -> None:
        self.run_install()

    @work(exclusive=True)
    async def run_install(self) -> None:
        decisions = {}
        for write in self.plan.conflicts:
            while True:
                choice = await self.app.push_screen_wait(ConflictScreen(write))
                if choice == "exit":
                    self.app.exit(None)
                    return
                if choice == "retry":
                    if os.path.lexists(write.target):
                        self.notify(f"{plan.shown(write.target)} still exists.", severity="warning")
                        continue
                    break
                decisions[write.target] = choice
                break
        try:
            self.app.result = install.execute(self.plan, version=self.app.version, decisions=decisions)
        except install.ManifestError as error:
            # Raised before anything is written. Carried out of the app so
            # __main__ prints it the way the non-interactive install does.
            self.app.result = error
        self.app.push_screen(ResultScreen())


class ConflictScreen(ModalScreen):
    """Dismisses with `overwrite`, `skip`, `retry` or `exit`."""

    def __init__(self, write):
        super().__init__()
        self.write = write

    def compose(self) -> ComposeResult:
        with Vertical(id="conflict"):
            yield Static(f"{plan.shown(self.write.target)} already exists.", classes="prompt", markup=False)
            yield Static(
                f"Installing {self.write.skill.name} for {self.write.agent.label} would replace it."
                " Remove or rename it yourself and choose Retry, choose Overwrite to replace it,"
                " or Skip to leave it and install the rest.",
                markup=False,
            )
            yield buttons(
                Button("Overwrite", id="overwrite", variant="error"),
                Button("Skip", id="skip"),
                Button("Retry", id="retry", variant="primary"),
                Button("Exit", id="exit"),
            )

    def on_mount(self) -> None:
        # A Content, not a str: a str title is read as markup, and a path may hold `[`.
        self.query_one("#conflict").border_title = Content(plan.shown(self.write.target))

    @on(Button.Pressed)
    def pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)


def summary(result) -> str:
    """The result screen's one line: what the install did, in total."""
    if isinstance(result, install.ManifestError):
        return "The install was refused. Nothing was written."
    missed = sum(1 for outcome in result if outcome.status != "written")
    if not missed:
        return "Every skill was written."
    return f"{missed} skill{'' if missed == 1 else 's'} {'was' if missed == 1 else 'were'} not written."


class ResultScreen(Screen):
    """What the install did, and the only way out of the interface.

    No Back: the plan the user confirmed is the only one that runs. Quit,
    `ctrl+q` and Escape all exit with `app.result`, so the installer prints what
    it wrote rather than reporting that nothing was installed.
    """

    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        result = self.app.result
        refused = isinstance(result, install.ManifestError)
        # markup off throughout, for the reason ConflictScreen gives: a target
        # path, and a manifest error's message, may hold `[`.
        yield Static(summary(result), classes="prompt", markup=False)
        with VerticalScroll(id="result"):
            yield Static(str(result) if refused else "\n".join(str(o) for o in result), markup=False)
        controls = [Button("Quit", id="quit", variant="primary")]
        if refused:
            controls.insert(0, Button("Copy", id="copy"))
        yield buttons(*controls)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#result").border_title = "Result"

    @on(Button.Pressed, "#copy")
    def copy_pressed(self) -> None:
        # OSC 52, which macOS Terminal drops; __main__ prints the message to
        # stderr as well, so it is available there too.
        self.app.copy_to_clipboard(str(self.app.result))
        self.notify("Copied the error message.")

    @on(Button.Pressed, "#quit")
    def quit_pressed(self) -> None:
        self.app.exit(self.app.result)
