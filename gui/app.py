import threading
import tkinter as tk
from tkinter import ttk
from gui.popups import show_error
from gui.login_frame import LoginFrame
from gui.register_frame import RegisterFrame


class SmartBiteApp(tk.Tk):
    """ Main window. Holds the engine and swaps between screens (frames).

    Every screen gets a reference to this app, so it can call:
        self.app.engine      -> the ProgressTrackingEngine (same methods as AppEngine + charts)
        self.app.show(name)  -> switch screen ("login", "register", "home", "dashboard")
        self.app.run_in_background(work, on_done) -> run slow AI calls without freezing the window
    """

    SCREENS = {"login": LoginFrame, "register": RegisterFrame} # name -> screen class. Each screen is added here as it gets built

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.title("SmartBite")
        self.geometry("900x650")
        self.minsize(760, 560)
        ttk.Style(self).theme_use("clam")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self._screens = {}
        for name, screen_class in self.SCREENS.items():
            screen = screen_class(container, self)
            screen.grid(row=0, column=0, sticky="nsew") # all stacked on top of each other, show() raises one
            self._screens[name] = screen
        self.show("login")

    
    # =========== Navigation ===========
    def show(self, name):
        screen = self._screens[name]
        if hasattr(screen, "on_show"): # lets a screen refresh itself (eg. dashboard redraws charts)
            screen.on_show()
        screen.tkraise()

    
    def logout(self):
        self.engine.logout()
        self.show("login")


    # =========== Background Work ===========
    def run_in_background(self, work, on_done):
        """ AI + Open Food Facts calls take seconds. Running them on the main thread freezes the window.
        work: function with no arguments that returns a result (or raises)
        on_done: function(result) called back on the main thread. Errors are shown as a popup instead. """
        box = {}

        def worker():
            try:
                box["result"] = work()
            except Exception as error: # noqa: BLE001 - shown to the user as a popup
                box["error"] = error

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        def check():
            if thread.is_alive():
                self.after(100, check) # tkinter is not thread safe, so poll from the main thread
            elif "error" in box:
                show_error(box["error"], self)
                on_done(None)
            else:
                on_done(box["result"])

        self.after(100, check)