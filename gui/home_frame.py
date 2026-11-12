from tkinter import ttk


class HomeFrame(ttk.Frame):
    """ Main screen: type a food (+ optional barcode) -> check_food -> maybe follow-up questions -> show Outcome. """

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app

        # ---- top bar ----
        top = ttk.Frame(self)
        top.pack(fill="x")
        self.welcome = ttk.Label(top, font=("Helvetica", 18, "bold"))
        self.welcome.pack(side="left")
        ttk.Button(top, text="Log out", command=app.logout).pack(side="right")
        ttk.Button(top, text="My progress", command=lambda: app.show("dashboard")).pack(side="right", padx=8)

    def on_show(self):
        profile = self.app.engine.profile
        self.welcome.config(text=f"Hi, {profile.username}" if profile else "")