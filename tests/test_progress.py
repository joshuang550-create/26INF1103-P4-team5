
import os
import shutil
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from matplotlib.figure import Figure

from exceptions.unexpected_error import UnexpectedError
from logic.verdict import Verdict
from progress.chart import FALLBACK_TEXT, Chart
from progress.chart_result import ChartResult
from progress.health_trend import HealthTrend
from progress.tracking_engine import ProgressTrackingEngine
from progress.trend_chart import TrendChart
from progress.verdict_log import VerdictLog
from progress.weekly_breakdown import WeeklyBreakdown
from progress.weekly_chart import WeeklyChart

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


# =========== Fakes and helpers ===========
def at(month, day):
    return datetime(2026, month, day, 12).timestamp()


def finished(verdict):
    return SimpleNamespace(outcome=SimpleNamespace(severity=verdict))  # like a FoodCheckStep with an Outcome




class FakeEngine:
    """Stands in for AppEngine so these tests need no AI, API key or data files."""
    def __init__(self, steps=(), username="jane"):
        self.steps = list(steps)
        self.profile = SimpleNamespace(username=username) if username else None
        self.checked = []

    def check_food(self, food_name, barcode=""):
        self.checked.append((food_name, barcode))
        return self.steps.pop(0)

    def answer_questions(self, answers):
        return self.steps.pop(0)

    def delete_account(self):
        self.profile = None

    def login(self, username, password):
        return f"logged in as {username}"


class ExplodingEngine:
    """An engine that fails in a way nobody planned for."""
    @property
    def profile(self):
        raise RuntimeError("engine exploded")


class BrokenChart(Chart):
    """A chart that can never be drawn but can still describe itself in words."""
    def render(self):
        raise RuntimeError("matplotlib exploded")

    def _describe(self):
        return "Plain text version"


class VeryBrokenChart(BrokenChart):
    def _describe(self):
        raise RuntimeError("the text version failed too")


class TempLogTestCase(unittest.TestCase):
    """Gives each test its own empty verdict_log.json path so tests never touch real data."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="smartbite_progress_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = os.path.join(self.tmp, "data", "verdict_log.json")
        self.log = VerdictLog(self.path)

    def write_raw(self, text):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            file.write(text)

    def read_raw(self):
        with open(self.path, encoding="utf-8") as file:
            return file.read()

    def tracker(self, *steps, engine=None):
        return ProgressTrackingEngine(engine or FakeEngine(steps), self.log)


# =========== Verdict history (data behind the graphs) ===========
class VerdictLogTests(TempLogTestCase):
    def test_entries_skip_records_without_a_valid_time_or_verdict(self):
        self.write_raw('{"jane": [{"verdict": "OK"}, {"time": "x", "verdict": "OK"}, "junk", {"time": 4}, {"time": 5, "verdict": "AVOID"}]}')
        self.assertEqual(self.log.entries("jane"), [(5, "AVOID")])

    def test_a_users_history_that_is_not_a_list_is_treated_as_empty(self):
        self.write_raw('{"jane": "broken"}')
        self.assertEqual(self.log.entries("jane"), [])
        self.log.add("jane", "Apple", "OK")  # and it gets replaced by a proper list on the next save
        self.assertEqual(self.log.verdicts("jane"), ["OK"])




# =========== Trend maths ===========
class HealthTrendTests(unittest.TestCase):
    def test_verdicts_become_scores_and_unknown_ones_are_ignored(self):
        self.assertEqual(HealthTrend(["OK", "MAYBE", "CAUTION", "AVOID"]).scores, [100, 50, 0])

    def test_rolling_average_uses_the_window(self):
        trend = HealthTrend(["AVOID", "OK", "OK", "OK"], window=3)
        self.assertEqual(trend.rolling_average(), [0, 50, 200 / 3, 100])

    def test_rolling_average_with_a_window_of_one_is_the_scores(self):
        self.assertEqual(HealthTrend(["OK", "AVOID", "CAUTION"], window=1).rolling_average(), [100, 0, 50])

    def test_rolling_average_of_nothing_is_empty(self):
        self.assertEqual(HealthTrend([]).rolling_average(), [])

    def test_direction_improving(self):
        self.assertEqual(HealthTrend(["AVOID", "AVOID", "OK", "OK"]).direction(), "improving")

    def test_direction_declining(self):
        self.assertEqual(HealthTrend(["OK", "OK", "AVOID", "CAUTION"]).direction(), "declining")

    def test_direction_steady(self):
        self.assertEqual(HealthTrend(["OK", "CAUTION", "OK", "CAUTION"]).direction(), "steady")

    def test_too_few_checks_gives_no_direction(self):
        self.assertEqual(HealthTrend(["OK", "OK", "OK"]).direction(), "not enough data")
        self.assertEqual(HealthTrend([]).direction(), "not enough data")

    def test_exactly_the_minimum_number_of_checks_is_judged(self):
        self.assertNotEqual(HealthTrend(["OK"] * HealthTrend.MIN_CHECKS).direction(), "not enough data")

    def test_a_change_just_under_ten_points_is_steady_and_ten_is_improving(self):
        # 8 checks, half = 4. earlier avg 50 (4 CAUTION). Recent: OK,CAUTION x3 -> 62.5 (12.5 rise)
        self.assertEqual(HealthTrend(["CAUTION"] * 4 + ["OK", "CAUTION", "CAUTION", "CAUTION"]).direction(), "improving")
        self.assertEqual(HealthTrend(["CAUTION"] * 8).direction(), "steady")
        # boundary: earlier 50, recent 60 (exactly CHANGE_NEEDED) -> improving
        trend = HealthTrend(["CAUTION"] * 5 + ["OK"] + ["CAUTION"] * 4)  # half = 5: earlier 50, recent 60
        self.assertEqual(trend.direction(), "improving")

    def test_odd_number_of_checks_ignores_the_middle_one(self):
        # half = 2, so the middle CAUTION is in neither half
        self.assertEqual(HealthTrend(["AVOID", "AVOID", "CAUTION", "OK", "OK"]).direction(), "improving")

    def test_unknown_verdicts_do_not_count_towards_the_minimum(self):
        self.assertEqual(HealthTrend(["OK", "OK", "OK", "MAYBE"]).direction(), "not enough data")


class SummaryTests(unittest.TestCase):
    def test_trend_summary_with_no_or_few_checks(self):
        self.assertIn("No food checks yet", HealthTrend([]).summary())
        self.assertIn("1 food check so far", HealthTrend(["OK"]).summary())
        self.assertIn("3 food checks so far", HealthTrend(["OK", "OK", "AVOID"]).summary())

    def test_trend_summary_describes_the_direction_and_counts(self):
        improving = HealthTrend(["AVOID", "AVOID", "OK", "OK"]).summary()
        self.assertIn("improving", improving)
        self.assertIn("2 OK, 0 CAUTION and 0 AVOID", improving)   # latest two
        self.assertIn("0 OK, 0 CAUTION and 2 AVOID", improving)   # earliest two
        self.assertIn("less healthy", HealthTrend(["OK", "OK", "AVOID", "AVOID"]).summary())
        self.assertIn("steady", HealthTrend(["OK", "CAUTION", "OK", "CAUTION"]).summary())

    def test_weekly_summary_with_no_checks(self):
        self.assertIn("No food checks yet", WeeklyBreakdown([]).summary())

    def test_weekly_summary_totals_and_latest_week(self):
        summary = WeeklyBreakdown([(at(11, 3), "OK"), (at(11, 4), "AVOID"), (at(11, 10), "OK")]).summary()
        self.assertIn("Over the last 2 weeks", summary)
        self.assertIn("3 food checks", summary)
        self.assertIn("2 OK, 0 CAUTION and 1 AVOID", summary)
        self.assertIn("starting 09 Nov", summary)

    def test_weekly_summary_uses_singular_for_one_week(self):
        self.assertIn("Over the last 1 week you", WeeklyBreakdown([(at(11, 3), "OK")]).summary())


# =========== Weekly grouping ===========
class WeeklyBreakdownTests(unittest.TestCase):
    def test_checks_are_counted_per_week_starting_monday(self):
        weeks = WeeklyBreakdown([(at(11, 3), "OK"), (at(11, 8), "AVOID"), (at(11, 9), "OK")]).weeks  # Tue, Sun, next Mon
        self.assertEqual(len(weeks), 2)
        self.assertEqual(weeks[0][0].isoformat(), "2026-11-02")
        self.assertEqual(weeks[0][1], {"OK": 1, "CAUTION": 0, "AVOID": 1})
        self.assertEqual(weeks[1][1], {"OK": 1, "CAUTION": 0, "AVOID": 0})

    def test_sunday_night_and_monday_morning_fall_in_different_weeks(self):
        late_sunday = datetime(2026, 11, 8, 23, 59).timestamp()
        early_monday = datetime(2026, 11, 9, 0, 1).timestamp()
        weeks = WeeklyBreakdown([(late_sunday, "OK"), (early_monday, "OK")]).weeks
        self.assertEqual([monday.isoformat() for monday, _ in weeks], ["2026-11-02", "2026-11-09"])

    def test_quiet_weeks_in_between_are_included_as_empty(self):
        weeks = WeeklyBreakdown([(at(10, 20), "OK"), (at(11, 10), "OK")]).weeks
        self.assertEqual(len(weeks), 4)
        self.assertEqual(weeks[1][1], {"OK": 0, "CAUTION": 0, "AVOID": 0})

    def test_only_the_most_recent_weeks_are_kept(self):
        entries = [(at(9, 7) + week * 7 * 86400, "OK") for week in range(12)]
        weeks = WeeklyBreakdown(entries, max_weeks=8).weeks
        self.assertEqual(len(weeks), 8)
        self.assertEqual(weeks[-1][0], WeeklyBreakdown(entries, max_weeks=99).weeks[-1][0])  # newest week survives

    def test_unsorted_entries_still_give_oldest_first(self):
        weeks = WeeklyBreakdown([(at(11, 10), "OK"), (at(11, 3), "OK")]).weeks
        self.assertLess(weeks[0][0], weeks[1][0])

    def test_unknown_verdicts_are_ignored_and_empty_input_is_fine(self):
        self.assertEqual(WeeklyBreakdown([(at(11, 3), "MAYBE")]).weeks, [])
        self.assertEqual(WeeklyBreakdown([]).weeks, [])



# =========== Drawing the charts ===========
class TrendChartTests(unittest.TestCase):
    def test_render_returns_a_figure_with_the_direction_label(self):
        figure = TrendChart(HealthTrend(["AVOID", "CAUTION", "OK", "OK"])).render()
        self.assertIsInstance(figure, Figure)
        self.assertIn("Improving", figure.axes[0].get_title(loc="right"))

    def test_each_direction_has_its_own_label(self):
        cases = {"▲ Improving": ["AVOID", "AVOID", "OK", "OK"], "▼ Declining": ["OK", "OK", "AVOID", "AVOID"],
                 "● Steady": ["OK", "CAUTION", "OK", "CAUTION"], "Not enough data yet": ["OK"]}
        for label, verdicts in cases.items():
            with self.subTest(label=label):
                self.assertEqual(TrendChart(HealthTrend(verdicts)).render().axes[0].get_title(loc="right"), label)

    def test_one_dot_per_check_at_the_right_height(self):
        axes = TrendChart(HealthTrend(["OK", "CAUTION", "AVOID"])).render().axes[0]
        dots = axes.collections[-1]
        self.assertEqual([y for _x, y in dots.get_offsets()], [100, 50, 0])

    def test_the_rolling_average_line_is_drawn(self):
        axes = TrendChart(HealthTrend(["AVOID", "OK", "OK", "OK"])).render().axes[0]
        self.assertEqual(list(axes.lines[0].get_ydata()), HealthTrend(["AVOID", "OK", "OK", "OK"]).rolling_average())

    def test_y_axis_is_labelled_with_verdicts(self):
        axes = TrendChart(HealthTrend(["OK", "AVOID"])).render().axes[0]
        self.assertEqual([label.get_text() for label in axes.get_yticklabels()], ["AVOID", "CAUTION", "OK"])

    def test_empty_history_shows_a_message(self):
        axes = TrendChart(HealthTrend([])).render().axes[0]
        self.assertEqual(axes.texts[0].get_text(), "No food checks yet")
        self.assertEqual(len(axes.lines), 0)

    def test_a_single_check_still_draws(self):
        self.assertIsInstance(TrendChart(HealthTrend(["AVOID"])).render(), Figure)

    def test_a_long_history_still_draws(self):
        self.assertIsInstance(TrendChart(HealthTrend(["OK", "CAUTION", "AVOID"] * 100)).render(), Figure)

    def test_save_writes_a_png(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "chart.png")
            TrendChart(HealthTrend(["OK", "AVOID"])).save(path)
            with open(path, "rb") as file:
                self.assertEqual(file.read(8), PNG_HEADER)


class WeeklyChartTests(unittest.TestCase):
    def test_bar_heights_match_the_weekly_counts(self):
        breakdown = WeeklyBreakdown([(at(11, 3), "OK"), (at(11, 4), "OK"), (at(11, 5), "AVOID"), (at(11, 10), "CAUTION")])
        axes = WeeklyChart(breakdown).render().axes[0]
        # bars are drawn OK, then CAUTION, then AVOID (2 weeks each)
        self.assertEqual([bar.get_height() for bar in axes.patches], [2, 0, 0, 1, 1, 0])

    def test_bars_are_labelled_with_the_week_start(self):
        axes = WeeklyChart(WeeklyBreakdown([(at(11, 3), "OK"), (at(11, 10), "OK")])).render().axes[0]
        self.assertEqual([label.get_text() for label in axes.get_xticklabels()], ["02 Nov", "09 Nov"])

    def test_bars_are_stacked(self):
        axes = WeeklyChart(WeeklyBreakdown([(at(11, 3), "OK"), (at(11, 4), "AVOID")])).render().axes[0]
        ok_bar, _caution_bar, avoid_bar = axes.patches
        self.assertEqual(ok_bar.get_y(), 0)
        self.assertEqual(avoid_bar.get_y(), 1)

    def test_empty_history_shows_a_message(self):
        axes = WeeklyChart(WeeklyBreakdown([])).render().axes[0]
        self.assertEqual(axes.texts[0].get_text(), "No food checks yet")
        self.assertEqual(len(axes.patches), 0)


class ChartBaseTests(unittest.TestCase):
    def test_the_base_class_cannot_be_used_directly(self):
        with self.assertRaises(TypeError):
            Chart()


# =========== What the GUI receives ===========
class ChartResultTests(unittest.TestCase):
    def test_a_working_chart_gives_a_graph_and_no_text(self):
        result = TrendChart(HealthTrend(["OK", "AVOID"])).result()
        self.assertIsInstance(result.graph, Figure)
        self.assertEqual(result.default, "")
        self.assertTrue(result.has_graph)

    def test_a_chart_that_cannot_be_drawn_gives_its_own_text(self):
        result = BrokenChart().result()
        self.assertIsNone(result.graph)
        self.assertEqual(result.default, "Plain text version")
        self.assertFalse(result.has_graph)

    def test_a_chart_that_cannot_even_describe_itself_gives_the_generic_message(self):
        self.assertEqual(VeryBrokenChart().result().default, FALLBACK_TEXT)

    def test_the_text_for_a_real_chart_comes_from_its_data(self):
        trend = HealthTrend(["AVOID", "AVOID", "OK", "OK"])
        with mock.patch.object(TrendChart, "render", side_effect=RuntimeError("boom")):
            result = TrendChart(trend).result()
        self.assertIsNone(result.graph)
        self.assertEqual(result.default, trend.summary())

    def test_weekly_chart_falls_back_to_its_summary_too(self):
        breakdown = WeeklyBreakdown([(at(11, 3), "OK")])
        with mock.patch.object(WeeklyChart, "render", side_effect=RuntimeError("boom")):
            result = WeeklyChart(breakdown).result()
        self.assertEqual(result.default, breakdown.summary())

    def test_the_result_cannot_be_changed(self):
        with self.assertRaises(FrozenInstanceError):
            ChartResult().default = "changed"


# =========== Tracking wrapper around AppEngine ===========
class TrackerChartTests(TempLogTestCase):
    """The two methods the dashboard calls. They must never raise."""

    def test_both_charts_come_back_as_graphs_when_everything_works(self):
        self.log.add("jane", "Apple", "OK")
        tracker = self.tracker()
        for result in (tracker.trend_chart(), tracker.weekly_chart()):
            self.assertIsInstance(result.graph, Figure)

    def test_a_user_with_no_checks_still_gets_a_graph(self):
        tracker = self.tracker()
        self.assertIsInstance(tracker.trend_chart().graph, Figure)
        self.assertIsInstance(tracker.weekly_chart().graph, Figure)

    def test_charts_show_checks_made_through_the_tracker(self):
        tracker = self.tracker(finished(Verdict.OK), finished(Verdict.AVOID))
        tracker.check_food("Apple")
        tracker.check_food("Prawns")
        dots = tracker.trend_chart().graph.axes[0].collections[-1]
        self.assertEqual([y for _x, y in dots.get_offsets()], [100, 0])

    def test_logged_out_gives_text_instead_of_raising(self):
        for chart in ("trend_chart", "weekly_chart"):
            with self.subTest(chart=chart):
                result = getattr(self.tracker(engine=FakeEngine(username=None)), chart)()
                self.assertIsNone(result.graph)
                self.assertIn("log in first", result.default)

    def test_unreadable_history_gives_text_instead_of_raising(self):
        self.write_raw("{corrupt")
        for chart in ("trend_chart", "weekly_chart"):
            with self.subTest(chart=chart):
                result = getattr(self.tracker(), chart)()
                self.assertIsNone(result.graph)
                self.assertIn("corrupted", result.default)

    def test_an_unexpected_failure_gives_the_default_error_text(self):
        for chart in ("trend_chart", "weekly_chart"):
            with self.subTest(chart=chart):
                result = getattr(self.tracker(engine=ExplodingEngine()), chart)()
                self.assertIsNone(result.graph)
                self.assertEqual(result.default, UnexpectedError().description)

    def test_a_drawing_failure_gives_the_text_summary(self):
        self.log.add("jane", "Apple", "OK")
        with mock.patch.object(WeeklyChart, "render", side_effect=RuntimeError("boom")):
            result = self.tracker().weekly_chart()
        self.assertIsNone(result.graph)
        self.assertIn("1 food check", result.default)


if __name__ == "__main__":
    unittest.main()