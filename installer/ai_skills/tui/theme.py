"""The installer's palette, and the one place it is written down.

installer.tcss names these only through theme variables (`$primary`, `$panel`
and so on), so changing a colour here changes every element that uses it.
`surface` is `background`, so no widget gets a fill the screen does not have.
`accent` is left unset, so Textual derives it from `primary`. The three banner
colours are not part of Textual's colour system, so they are extra variables
(`$banner-start`, `$banner-end`, `$banner-border`), and banner.py reads the
gradient's two ends from them. The App also gives them as defaults, because
installer.tcss fails to parse under a theme that lacks them, and the command
palette can switch to any built-in theme.
"""

from textual.theme import Theme

BACKGROUND = "#101010"
PRIMARY = "#FF9F43"
SECONDARY = "#74B9FF"
ERROR = "#FF7675"
WARNING = "#FDCB6E"
SUCCESS = "#55EFC4"
PANEL = "#555555"
FOREGROUND = "#DDDDDD"
BANNER_START = "#FF9900"
BANNER_END = "#FFCC00"
BANNER_BORDER = "#FF9900"

BANNER_VARIABLES = {
    "banner-start": BANNER_START,
    "banner-end": BANNER_END,
    "banner-border": BANNER_BORDER,
}

AI_SKILLS_THEME = Theme(
    name="ai-skills",
    primary=PRIMARY,
    secondary=SECONDARY,
    warning=WARNING,
    error=ERROR,
    success=SUCCESS,
    foreground=FOREGROUND,
    background=BACKGROUND,
    surface=BACKGROUND,
    panel=PANEL,
    dark=True,
    variables=BANNER_VARIABLES,
)
