from progress.chart import COLORS, MUTED, Chart
from progress.weekly_breakdown import VERDICTS


class WeeklyChart(Chart):
    """Draws a WeeklyBreakdown as stacked bars: how the mix of verdicts changes week by week."""

    def __init__(self, breakdown):
        self._breakdown = breakdown

    def render(self):
        figure, axes = self._blank_axes("Weekly verdict mix")
        weeks = self._breakdown.weeks

        if not weeks:
            self._show_message(axes, "No food checks yet")
            return figure

        labels = [monday.strftime("%d %b") for monday, _counts in weeks]
        bottoms = [0] * len(weeks)
        for verdict in VERDICTS:
            counts = [week[verdict] for _monday, week in weeks]
            bars = axes.bar(labels, counts, bottom=bottoms, width=0.62, color=COLORS[verdict],
                            edgecolor="white", linewidth=1.5, label=verdict)
            axes.bar_label(bars, labels=[str(count) if count else "" for count in counts],
                           label_type="center", color="white", fontweight="bold")
            bottoms = [bottom + count for bottom, count in zip(bottoms, counts)]

        axes.margins(y=0.1)  # headroom above the tallest bar
        axes.set_xlabel("Week starting", color=MUTED)
        axes.set_ylabel("Food checks", color=MUTED)
        axes.yaxis.get_major_locator().set_params(integer=True)
        figure.legend(loc="outside lower center", ncols=3, frameon=False)
        return figure