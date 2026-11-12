from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DashboardFrame(ttk.Frame):
    """ Progress screen. trend_chart()/weekly_chart() never raise: they return a ChartResult
    with either .graph (matplotlib Figure) or .default (text to show instead). """

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


    def on_show(self): # redraw every time, so new checks appear
        self._draw(self.trend_tab, self.app.engine.trend_chart())
        self._draw(self.weekly_tab, self.app.engine.weekly_chart())
        

    @staticmethod
    def _draw(tab, chart_result):
        for child in tab.winfo_children():
            child.destroy()
        if chart_result.has_graph:
            canvas = FigureCanvasTkAgg(chart_result.graph, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ttk.Label(tab, text=chart_result.default, wraplength=600, justify="center").pack(expand=True)