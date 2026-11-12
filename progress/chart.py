from abc import ABC, abstractmethod

from matplotlib.figure import Figure

from progress.chart_result import ChartResult

COLORS = {"OK": "#3ba776", "CAUTION": "#f2b134", "AVOID": "#E5534B"}
TEXT = "#2b2f36"
MUTED = "#8a9099"
GRID = "#e6e8ec"

FALLBACK_TEXT = "There was an issue generating your dashboard, please try again later."


class Chart(ABC):
    """ shared look for dashboard chart. subclasses draw respective own content"""

    @abstractmethod
    def render(self):
        pass # returns matplotlib fig

    @abstractmethod
    def _describe(self):
        pass # text if graph cannot be drawn

    def result(self):
        """ GUI - nvr raises: a ChartResult with graph, or text to show instead """
        try:
            return ChartResult(graph=self.render())
        # GUI always get something back, so nth escape
        except Exception: # noqa: BLE001
            return self._text_result()

    def save(self, path):
        self.render().savefig(path, dpi=150, bbox_inches="tight", facecolor="white")

    # ========== helpers ==========
    def _text_result(self):
        try:
            return ChartResult(default=self._describe())
        # text version fail not escape
        except Exception: # noqa: BLE001
            return ChartResult(default=FALLBACK_TEXT)

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