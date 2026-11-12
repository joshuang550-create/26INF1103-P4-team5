from tkinter import ttk


class DashboardFrame(ttk.Frame):
    """ Progress screen with a tab for each chart. """

    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="My progress", font=("Helvetica", 18, "bold")).pack(side="left")
        ttk.Button(top, text="Back", command=lambda: app.show("home")).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, pady=(12, 0))
        self.trend_tab = ttk.Frame(self.tabs)
        self.weekly_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.trend_tab, text="Trend")
        self.tabs.add(self.weekly_tab, text="Weekly")