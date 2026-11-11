from abc import ABC, abstractmethod

from matplotlib.figure import Figure

COLORS = {"OK": "#3ba776", "CAUTION": "#f2b134", "AVOID": "#E5534B"}
TEXT = "#2b2f36"
MUTED = "#8a9099"
GRID = "#e6e8ec"


class Chart(ABC):
    """ shared look for dashboard chart. subclasses draw respective own content"""

    @abstractmethod
    def render(self):
        pass # returns matplotlib fig

    def save(self, path):
        self.render().savefig(path, dpi=150, bbox_inches="tight", facecolor="white")

    # ========== subclass helpers ==========
    def _blank_axes(self, title):
        figure = Figure(figsize=(7.5, 4.6), layout="constrained")
        axes = figure.subplots()
        axes.set_facecolor("#FBFBFD")
        for side in ("top", "right"):
            axes.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            axes.spines[side].set_color(GRID)
        axes.tick_params(colors=MUTED, length=0)
        axes.yaxis.grid(True, color=GRID)
        axes.set_axisbelow(True)
        axes.set_title(title, loc="left", fontsize=14, fontweight="bold", color=TEXT)
        return figure, axes

    @staticmethod
    def _show_message(axes, text):
        axes.text(0.5, 0.5, text, ha="center", va="center", transform=axes.transAxes, color=MUTED, fontsize=12)
        axes.set_xticks([])
        axes.set_yticks([])
        axes.grid(False)