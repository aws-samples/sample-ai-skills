"""Toggles that show their state in the glyph, not only in its colour.

Both override how Textual 8.2.8 draws a toggle, which is not public API, so
test_appearance.py pins what they draw and a Textual upgrade that changes it
fails there (design D1 and D2 of
openspec/changes/archive/2026-09-30-checkbox-bracket-glyphs).
uv.lock pins 8.2.8, but `uvx --from git+…` does not read it, so a user can run
a newer Textual first; on a layout they do not know, both draw Textual's own.
Their colours are in installer.tcss, by component class.
"""

from rich.segment import Segment
from textual.content import Content
from textual.strip import Strip
from textual.widgets import RadioButton, SelectionList
from textual.widgets.option_list import OptionDoesNotExist

#: What Textual 8.2.8's SelectionList draws before each prompt, one segment each.
STOCK_PREFIX = ["▐", "X", "▌", " "]


class CheckList(SelectionList):
    """A SelectionList whose rows begin `[✓] ` when checked and `[ ] ` when not."""

    def render_line(self, y: int) -> Strip:
        line = super().render_line(y)
        try:
            option = self.get_option_at_index(self.scroll_offset.y + y)
        except OptionDoesNotExist:
            return line
        segments = list(line)
        if [segment.text for segment in segments[:4]] != STOCK_PREFIX:
            return line
        # The `X` is styled by the selection-list--button* class for the row
        # and carries the row's click meta, so the brackets take its style and
        # stay clickable.
        inner = segments[1]
        mark = "✓" if option.value in self.selected else " "
        return Strip([Segment(char, inner.style) for char in ("[", mark, "]")] + segments[3:])


class ScopeOption(RadioButton):
    """A RadioButton drawn as `◉` when chosen and `◯` when not, with no brackets.

    The glyph carries a trailing cell in the button's own style, so the label's
    highlighted padding does not start in the cell next to the glyph."""

    @property
    def _button(self) -> Content:
        return Content.styled("◉ " if self.value else "◯ ", self.get_visual_style("toggle--button"))
