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
    
        form = ttk.LabelFrame(self, text="Check a food", padding=12)
        form.pack(fill="x", pady=16)
        ttk.Label(form, text="Food name").grid(row=0, column=0, sticky="w")
        self.food = ttk.Entry(form, width=40)
        self.food.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Barcode (optional)").grid(row=1, column=0, sticky="w")
        self.barcode = ttk.Entry(form, width=20)
        self.barcode.grid(row=1, column=1, sticky="w", padx=8, pady=4)
        self.check_button = ttk.Button(form, text="Check")
        self.check_button.grid(row=0, column=2, rowspan=2, padx=8)
        self.status = ttk.Label(form, foreground="#8a9099")
        self.status.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))