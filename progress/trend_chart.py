from matplotlib.figure import Figure

POINT_COLORS = {100: "#2e9e5b", 50: "#e0a526", 0: "#d64545"} # OK, CAUTION, AVOID


class TrendChart:
    """ draws a HealthTrend: one dot per check plus rolling-average line."""

    def __init__(self, trend):
        self._trend = trend

    def render(self):
        figure = Figure(figsize=(7, 4.5))
        axes = figure.subplots()
        scores = self._trend.scores

        if not scores:
            axes.text(0.5, 0.5, "No food checks yet", ha="center", va="center", transform=axes.transAxes, color="gray")
            axes.set_xticks([])
            axes.set_yticks([])
        else:
            checks = list(range(1, len(scores) + 1))
            axes.plot(checks, self._trend.rolling_average(), color="#3b6fb6", label="Trend (rolling average)")
            axes.scatter(checks, scores, c=[POINT_COLORS[score] for score in scores], zorder=3)
            axes.set_ylim(-10, 110)
            axes.set_yticks([0, 50, 100])
            axes.set_yticklabels(["AVOID", "CAUTION", "OK"])
            axes.xaxis.get_major_locator().set_params(integer=True)
            axes.set_xlabel("Check number (oldest to newest)")
            axes.legend()

        axes.set_title(f"Food check trend: {self._trend.direction()}")
        return figure

    def save(self, path):
        self.render().savefig(path, dpi=150, bbox_inches="tight")
