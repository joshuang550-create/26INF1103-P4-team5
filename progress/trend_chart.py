from progress.chart import COLORS, MUTED, Chart

LINE_COLOR = "#3B6FB6"
DIRECTIONS = {  
    "improving": ("▲ Improving", COLORS["OK"]),
    "declining": ("▼ Declining", COLORS["AVOID"]),
    "steady": ("● Steady", COLORS["CAUTION"]),
    "not enough data": ("Not enough data yet", MUTED),
}


class TrendChart(Chart):
    """ Draws HealthTrend: one dot per check, rolling-average line and bg coloured zones. """

    def __init__(self, trend):
        self._trend = trend

    def render(self):
        figure, axes = self._blank_axes("Food check trend")
        scores = self._trend.scores

        label, colour = DIRECTIONS[self._trend.direction()]
        axes.set_title(label, loc="right", fontsize=12, fontweight="bold", color=colour)

        if not scores:
            self._show_message(axes, "No food checks yet")
            return figure

        checks = list(range(1, len(scores) + 1))
        average = self._trend.rolling_average()

        # bg coloured zones behind the data: AVOID>CAUTION>OK, bottom>top
        axes.axhspan(-10, 25, color=COLORS["AVOID"], alpha=0.08, linewidth=0)
        axes.axhspan(25, 75, color=COLORS["CAUTION"], alpha=0.08, linewidth=0)
        axes.axhspan(75, 110, color=COLORS["OK"], alpha=0.08, linewidth=0)

        axes.plot(checks, average, color=LINE_COLOR, linewidth=2.5, label="Trend (rolling average)")
        axes.scatter(checks, scores, s=110, c=[self._dot_colour(score) for score in scores],
                     edgecolors="white", linewidths=1.8, zorder=3)

        axes.set_ylim(-10, 110)
        axes.set_yticks([0, 50, 100])
        axes.set_yticklabels(["AVOID", "CAUTION", "OK"], fontweight="bold")
        axes.xaxis.get_major_locator().set_params(integer=True)
        axes.set_xlabel("Check number (oldest to newest)", color=MUTED)
        axes.legend(loc="lower right", frameon=False)
        return figure

    @staticmethod
    def _dot_colour(score):
        return COLORS["OK"] if score == 100 else COLORS["CAUTION"] if score == 50 else COLORS["AVOID"]

    def _describe(self):
        return self._trend.summary()
