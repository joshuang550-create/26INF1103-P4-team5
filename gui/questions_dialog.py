import tkinter as tk
from tkinter import ttk
from gui.popups import center_on_screen


class QuestionsDialog(tk.Toplevel):
    """ Popup that asks the AI's follow-up questions.
    After it closes, .answers is {question: answer} or None if the user cancelled. """

    def __init__(self, parent, questions):
        super().__init__(parent)
        self.title("A few more details")
        self.transient(parent)
        self.resizable(False, False)
        self.answers = None
        self._entries = {}

        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="SmartBite needs a bit more information:", font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(0, 10))

        for question in questions:
            ttk.Label(body, text=question, wraplength=420, justify="left").pack(anchor="w", pady=(6, 2))
            entry = ttk.Entry(body, width=55)
            entry.pack(anchor="w")
            self._entries[question] = entry

        buttons = ttk.Frame(body)
        buttons.pack(anchor="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel check", command=self.destroy).pack(side="right")
        ttk.Button(buttons, text="Submit", command=self._submit).pack(side="right", padx=8)

        self.protocol("WM_DELETE_WINDOW", self.destroy) # closing the window = cancel
        next(iter(self._entries.values())).focus_set()
        center_on_screen(self)
        self.grab_set() # modal: block the main window until answered        
        
        self.grab_set() # modal: block the main window until answered

    def _submit(self):
        self.answers = {question: entry.get() for question, entry in self._entries.items()} # engine checks none are empty
        self.destroy()