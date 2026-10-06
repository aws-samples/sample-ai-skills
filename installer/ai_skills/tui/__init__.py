"""The Textual interface: agents, skills, scope, confirmation.

It only collects a selection. What gets written is decided by `plan.build` and
done by `install.execute`, the same two calls `--yes` makes, so the interface
and the flags cannot disagree about an install.

Each step is a Screen pushed onto the stack; Back pops it, so the earlier
screen is exactly as the user left it, and what each screen chose is kept on
the App so a screen pushed again starts from it.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from textual.app import App

from .screens import AgentsScreen
from .theme import AI_SKILLS_THEME, BANNER_VARIABLES


@dataclass
class Selection:
    agents: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    scope: str = "user"


class InstallerApp(App):
    """Exits with the install's result: the outcomes, an `install.ManifestError`
    when a manifest refused the install, or None when the user left first."""

    TITLE = "ai-skills"
    # Resolved against this file's directory, so it travels inside the wheel.
    CSS_PATH = "installer.tcss"

    def __init__(self, catalog, *, version: str, cwd: Path, home: Path, env=os.environ, selection=None):
        super().__init__()
        # Here rather than in on_mount, so the first frame is already drawn in it.
        self.register_theme(AI_SKILLS_THEME)
        self.theme = AI_SKILLS_THEME.name
        self.catalog = catalog
        self.version = version
        self.cwd = cwd
        self.home = home
        self.env = env
        self.selection = selection or Selection()
        #: What the install produced, once it has run. None until then.
        self.result = None

    def get_theme_variable_defaults(self) -> dict[str, str]:
        return {**super().get_theme_variable_defaults(), **BANNER_VARIABLES}

    # `ctrl+q` is App.BINDINGS' own priority binding, so a screen cannot rebind
    # it; overriding the action it runs is what makes every way out of the result
    # screen return the install's result rather than None.
    async def action_quit(self) -> None:
        self.exit(self.result)

    def on_mount(self) -> None:
        self.push_screen(AgentsScreen())
