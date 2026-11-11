import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from matplotlib.figure import Figure

from managers.logic_manager import Verdict
from models.errors import DataError, InvalidActionError
from progress.health_trend import HealthTrend
from progress.trend_chart import TrendChart
from progress.tracking_engine import ProgressTrackingEngine
from progress.verdict_log import VerdictLog


def finished(verdict):
    return SimpleNamespace(outcome=SimpleNamespace(severity=verdict))  # like FoodCheckStep with an Outcome


ASKING = SimpleNamespace(outcome=None)  # like FoodCheckStep that still needs ans
FALLBACK = SimpleNamespace(outcome=SimpleNamespace(severity=None))  # like RecommendationOutcome


class FakeEngine:
    """ Stands in for AppEngine so tests no need AI,API key and files. """

    def __init__(self, steps):
        self.steps = list(steps)
        self.profile = SimpleNamespace(username="jane")

    def check_food(self, food_name, barcode=""):
        return self.steps.pop(0)

    def answer_questions(self, answers):
        return self.steps.pop(0)

    def delete_account(self):
        self.profile = None

    def login(self, username, password):
        return f"logged in as {username}"


class TempFolderTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "data" / "verdict_log.json"


class VerdictLogTests(TempFolderTestCase):
    def setUp(self):
        super().setUp()
        self.log = VerdictLog(self.path)

    def test_verdicts_come_back_in_order(self):
        self.log.add("jane", "Apple", "OK")
        self.log.add("jane", "Prawn Crackers", "AVOID")
        self.assertEqual(self.log.verdicts("jane"), ["OK", "AVOID"])

    def test_users_are_kept_separate(self):
        self.log.add("jane", "Apple", "OK")
        self.assertEqual(self.log.verdicts("ride"), [])

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(self.log.verdicts("jane"), [])

    def test_corrupt_file_raises_data_error_and_is_not_overwritten(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json", encoding="utf-8")
        with self.assertRaises(DataError):
            self.log.verdicts("jane")
        with self.assertRaises(DataError):
            self.log.add("jane", "Apple", "OK")
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{not json")

    def test_wrong_shape_file_raises_data_error(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("[]", encoding="utf-8")
        with self.assertRaises(DataError):
            self.log.verdicts("jane")

    def test_delete_removes_only_that_user(self):
        self.log.add("jane", "Apple", "OK")
        self.log.add("ride", "Apple", "OK")
        self.log.delete("jane")
        self.assertEqual(self.log.verdicts("jane"), [])
        self.assertEqual(self.log.verdicts("ride"), ["OK"])


class HealthTrendTests(unittest.TestCase):
    def test_verdicts_become_scores_and_unknown_ones_are_ignored(self):
        self.assertEqual(HealthTrend(["OK", "MAYBE", "CAUTION", "AVOID"]).scores, [100, 50, 0])

    def test_rolling_average(self):
        trend = HealthTrend(["AVOID", "OK", "OK", "OK"], window=3)
        self.assertEqual(trend.rolling_average(), [0, 50, 200 / 3, 100])

    def test_direction_improving(self):
        self.assertEqual(HealthTrend(["AVOID", "AVOID", "OK", "OK"]).direction(), "improving")

    def test_direction_declining(self):
        self.assertEqual(HealthTrend(["OK", "OK", "AVOID", "CAUTION"]).direction(), "declining")

    def test_direction_steady(self):
        self.assertEqual(HealthTrend(["OK", "CAUTION", "OK", "CAUTION"]).direction(), "steady")

    def test_too_few_checks(self):
        self.assertEqual(HealthTrend(["OK", "OK", "OK"]).direction(), "not enough data")
        self.assertEqual(HealthTrend([]).direction(), "not enough data")


class TrendChartTests(unittest.TestCase):
    def test_render_returns_a_figure(self):
        figure = TrendChart(HealthTrend(["AVOID", "CAUTION", "OK", "OK"])).render()
        self.assertIsInstance(figure, Figure)
        self.assertIn("improving", figure.axes[0].get_title())

    def test_empty_history_shows_a_message(self):
        figure = TrendChart(HealthTrend([])).render()
        self.assertEqual(figure.axes[0].texts[0].get_text(), "No food checks yet")

    def test_save_writes_a_png(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "chart.png"
            TrendChart(HealthTrend(["OK", "AVOID"])).save(path)
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


class ProgressTrackingEngineTests(TempFolderTestCase):
    def setUp(self):
        super().setUp()
        self.log = VerdictLog(self.path)

    def tracker(self, *steps):
        return ProgressTrackingEngine(FakeEngine(steps), self.log)

    def test_finished_check_records_its_verdict(self):
        tracker = self.tracker(finished(Verdict.CAUTION))
        tracker.check_food("Heinz Beanz")
        self.assertEqual(self.log.verdicts("jane"), ["CAUTION"])

    def test_check_that_is_still_asking_questions_records_nothing_until_answered(self):
        tracker = self.tracker(ASKING, finished(Verdict.OK))
        tracker.check_food("Noodles")
        self.assertEqual(self.log.verdicts("jane"), [])
        tracker.answer_questions({"How big was the bowl?": "Large"})
        self.assertEqual(self.log.verdicts("jane"), ["OK"])

    def test_fallback_has_no_verdict_so_nothing_is_recorded(self):
        self.tracker(FALLBACK).check_food("Mystery food")
        self.assertEqual(self.log.verdicts("jane"), [])

    def test_the_step_is_returned_unchanged(self):
        step = finished(Verdict.AVOID)
        self.assertIs(self.tracker(step).check_food("Prawns"), step)

    def test_other_methods_pass_through_to_the_engine(self):
        self.assertEqual(self.tracker().login("jane", "pw"), "logged in as jane")

    def test_delete_account_also_deletes_the_history(self):
        tracker = self.tracker(finished(Verdict.OK))
        tracker.check_food("Apple")
        tracker.delete_account()
        self.assertEqual(self.log.verdicts("jane"), [])

    def test_progress_trend_uses_the_logged_in_users_verdicts(self):
        tracker = self.tracker(*[finished(v) for v in (Verdict.AVOID, Verdict.AVOID, Verdict.OK, Verdict.OK)])
        for _ in range(4):
            tracker.check_food("Food")
        self.assertEqual(tracker.progress_trend().direction(), "improving")

    def test_progress_trend_needs_a_logged_in_user(self):
        tracker = self.tracker()
        tracker.delete_account()
        with self.assertRaises(InvalidActionError):
            tracker.progress_trend()

    def test_a_history_problem_does_not_lose_the_result(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{corrupt", encoding="utf-8")
        step = finished(Verdict.AVOID)
        self.assertIs(self.tracker(step).check_food("Prawns"), step)


if __name__ == "__main__":
    unittest.main()