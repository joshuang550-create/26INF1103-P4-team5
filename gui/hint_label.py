from tkinter import font, ttk

from managers.io_manager import FieldCheck

PROBLEM_COLOUR = "#E5534B"
SUGGESTION_COLOUR = "#2f6fb5"


class HintLabel(ttk.Label):
    """ Small text next to a field. Red for a problem. Blue and underlined for a suggestion,
    which the user can click to accept. """

    def __init__(self, parent, on_accept=None, **options):
        super().__init__(parent, foreground=PROBLEM_COLOUR, **options)
        self._fix = None
        self._on_accept = on_accept # function(fix) called when the user clicks a suggestion
        self._plain_font = font.nametofont("TkDefaultFont")
        self._link_font = self._plain_font.copy()
        self._link_font.configure(underline=True)
        self.bind("<Button-1>", lambda _event: self._accept())

    def show(self, check): # check is a FieldCheck from IOManager
        self._fix = check.fix
        if check.fix:
            self.config(text=check.message, foreground=SUGGESTION_COLOUR, font=self._link_font, cursor="hand2")
        else:
            self.config(text=check.message, foreground=PROBLEM_COLOUR, font=self._plain_font, cursor="")

    def clear(self):
        self.show(FieldCheck())

    def _accept(self):
        if self._fix and self._on_accept:
            self._on_accept(self._fix)