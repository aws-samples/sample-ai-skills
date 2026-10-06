"""The intro screen's banner, drawn as rich-pyfiglet 2.0.1's `gradient_down` draws it.

rich-pyfiglet animates with a blocking `rich.live.Live` loop, which cannot run
inside a Textual app, so a Textual timer redraws the frames here instead
(design D1 of openspec/changes/animate-installer-banner). The gradient's two
ends are the theme's `$banner-start` and `$banner-end`; the border is in
installer.tcss.
"""

from rich.style import Style
from rich.text import Text
from textual.color import Color
from textual.widgets import Static

#: "AI-Skills" in figlet's ansi_regular font, with trailing whitespace and the
#: blank rows stripped. A constant, so no figlet dependency.
BANNER = """ █████  ██       ███████ ██   ██ ██ ██      ██      ███████
██   ██ ██       ██      ██  ██  ██ ██      ██      ██
███████ ██ █████ ███████ █████   ██ ██      ██      ███████
██   ██ ██            ██ ██  ██  ██ ██      ██           ██
██   ██ ██       ███████ ██   ██ ██ ███████ ███████ ███████"""

#: rich-pyfiglet's default frame rate.
FPS = 5


def gradient(start: Color, end: Color, steps: int) -> list:
    """`steps` colours from `start` to `end`, both included, as rich-pyfiglet's `make_gradient`."""
    return [start.blend(end, i / (steps - 1)) for i in range(steps)]


class Banner(Static):
    """Row `i` is `cycle[(i + position) % len(cycle)]`, and each frame decrements `position`.

    The cycle blends from start to end in one step per row and back again in as
    many, so no row ever changes from the end colour straight to the start colour.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows = BANNER.splitlines()
        self.cycle = []
        self.position = 0
        self.timer = None

    def on_mount(self) -> None:
        variables = self.app.get_css_variables()
        start, end = Color.parse(variables["banner-start"]), Color.parse(variables["banner-end"])
        rows = len(self.rows)
        self.cycle = gradient(start, end, rows) + gradient(end, start, rows)
        self.update(self.frame())
        # TEXTUAL_ANIMATIONS=none keeps the first frame.
        if self.app.animation_level != "none":
            self.timer = self.set_interval(1 / FPS, self.advance)

    def frame(self) -> Text:
        colours = [self.cycle[(i + self.position) % len(self.cycle)] for i in range(len(self.rows))]
        return Text("\n").join(Text(row, Style(color=c.rich_color)) for row, c in zip(self.rows, colours))

    def advance(self) -> None:
        self.position -= 1
        self.update(self.frame())

    # The intro screen calls these as it is covered and uncovered, so the banner
    # does not redraw behind the other screens.
    def pause(self) -> None:
        if self.timer is not None:
            self.timer.pause()

    def resume(self) -> None:
        if self.timer is not None:
            self.timer.resume()
