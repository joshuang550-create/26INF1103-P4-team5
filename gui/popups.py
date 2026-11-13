import tkinter as tk
from tkinter import ttk

from models.errors import as_app_error


def center_on_screen(window):
    """ Moves a window to the middle of the screen. Call it after the window's widgets are built. """
    window.update_idletasks() # lets tkinter work out how big the window is first
    width, height = window.winfo_width(), window.winfo_height()
    if width <= 1: # not drawn yet, use the size it asks for
        width, height = window.winfo_reqwidth(), window.winfo_reqheight()
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"+{x}+{y}")


# =========== Popup Card ===========
CARD_COLOUR = "white"
SHADOW_COLOURS = ("#d3d1cc", "#c4c2bd", "#b3b1ac") # outside to inside, a soft edge around the card
BUTTON_COLOUR = "#1a73e8" # Google blue
BUTTON_HOVER = "#e8f0fe"


class Popup:
    """ A small card in the middle of the app window, like the dialogs on Google's sites.
    It is not a separate window, sits on top of the current screen, and the rest of the app
    is locked until a button is clicked. After it closes, .answer is the button clicked. """

    def __init__(self, parent, title, message, buttons=("OK",)):
        self.answer = None
        window = parent.winfo_toplevel()

        self._outer = holder = tk.Frame(window, bg=SHADOW_COLOURS[0]) # each layer is 1px of shadow
        for colour in SHADOW_COLOURS[1:]:
            layer = tk.Frame(holder, bg=colour)
            layer.pack(padx=1, pady=1)
            holder = layer
        card = tk.Frame(holder, bg=CARD_COLOUR, padx=24, pady=20)
        card.pack(padx=1, pady=1)

        tk.Label(card, text=title, bg=CARD_COLOUR, fg="#202124", font=("Helvetica", 16, "bold")).pack(anchor="w")
        tk.Label(card, text=message, bg=CARD_COLOUR, fg="#3c4043", wraplength=340, justify="left").pack(anchor="w", pady=(8, 16))

        row = tk.Frame(card, bg=CARD_COLOUR)
        row.pack(anchor="e")
        for text in buttons:
            self._text_button(row, text, bold=(text == buttons[-1])).pack(side="left", padx=(8, 0))

        self._outer.bind("<Return>", lambda _event: self._close(buttons[0])) # Enter = first button ("No" on a yes/no card)
        self._outer.bind("<Escape>", lambda _event: self._close(None))
        self._outer.place(relx=0.5, rely=0.5, anchor="center") # middle of the app window, on top of everything
        self._outer.lift()
        self._outer.focus_set()
        self._outer.grab_set() # only the card can be clicked until it closes
        window.wait_window(self._outer) # pause here until a button is clicked

    def _text_button(self, parent, text, bold):
        """ A flat blue text button. A tk.Label is used because macOS ignores colours on real buttons. """
        button = tk.Label(parent, text=text.upper(), bg=CARD_COLOUR, fg=BUTTON_COLOUR, padx=12, pady=6,
                          cursor="hand2", font=("Helvetica", 12, "bold" if bold else "normal"))
        button.bind("<Button-1>", lambda _event: self._close(text))
        button.bind("<Enter>", lambda _event: button.config(bg=BUTTON_HOVER))
        button.bind("<Leave>", lambda _event: button.config(bg=CARD_COLOUR))
        return button

    def _close(self, answer):
        self.answer = answer
        self._outer.destroy()


# =========== Shortcuts ===========
def show_error(error, parent=None):
    """ Every SmartBiteError has a title and description, so one card works for all of them.
    Anything unplanned becomes UnexpectedError (default title + description) via as_app_error. """
    problem = as_app_error(error)
    Popup(parent, problem.title, problem.description)


def show_info(title, message, parent=None):
    Popup(parent, title, message)


def ask_yes_no(title, message, parent=None):
    return Popup(parent, title, message, buttons=("No", "Yes")).answer == "Yes" # True or False