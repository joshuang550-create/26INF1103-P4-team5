"""GUI feature only: popups, live-hint label, every screen (login, register, home, dashboard, profile),
the follow-up questions dialog and window navigation.

The GUI is tested with real tkinter widgets but a fake IOManager / engine (unittest.mock), so no AI, files or
network are used. A display is needed to create windows; if there is none (for example a bare Linux server),
the whole file is skipped. Run it with:  python -m unittest tests.test_gui -v
"""
import os
import sys
import time
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest import mock

# lets this file also be run directly (python tests/test_gui.py) by putting the project root on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tests  # noqa: E402,F401  (installs stand-ins for missing third-party libraries)

from matplotlib.figure import Figure

from exceptions.data_error import DataError
from exceptions.login_failed_error import LoginFailedError
from exceptions.unexpected_error import UnexpectedError
from gui import popups
from gui.app import SmartBiteApp
from gui.hint_label import PROBLEM_COLOUR, SUGGESTION_COLOUR, HintLabel
from gui.home_frame import VERDICT_COLOURS
from gui.questions_dialog import QuestionsDialog
from models.field_check import FieldCheck
from progress.chart_result import ChartResult


def setUpModule():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        if os.environ.get("SMARTBITE_REQUIRE_GUI_TESTS") == "1":
            raise RuntimeError(
                "GUI tests require a working display. Run with xvfb-run -a "
                "and ensure that Tk/Tcl libraries are installed."
            ) from error
        raise unittest.SkipTest(f"no display available for tkinter: {error}")
    root.destroy()


# =========== Fakes and helpers ===========
def make_profile(**overrides):
    values = dict(username="jane", gender="female", ethnicity="Chinese", age=30, height=165.0, weight=55.0,
                  country="Singapore", medical_conditions=["asthma", "peanut allergy"])
    values.update(overrides)
    return SimpleNamespace(**values)


def assessment_outcome(headline="AVOID", **details):
    content = {"reason": "Very salty.", "portion_g": 100, "nutrients": {"sodium_mg": 900}, "potential_concern": True,
               "flags": [{"nutrient": "sodium_mg", "value": 900, "level": "high"}],
               "allergens_found": {"tree_nuts": ["almond"]}, "confidence": 8}
    content.update(details)
    return SimpleNamespace(headline=headline, severity=headline, details=lambda: content)


def fallback_outcome(recommendations=({"food": "Apple", "reason": "Light and sweet."},)):
    content = {"message": "We cannot decide.", "recommendations": list(recommendations)}
    return SimpleNamespace(headline="UNDETERMINED", severity=None, details=lambda: content)


def step(outcome=None, questions=()):
    return SimpleNamespace(needs_answers=outcome is None, questions=list(questions), outcome=outcome)


def pump(window, seconds=0.0):
    """Let tkinter handle pending events (and timers) for a short while."""
    end = time.time() + seconds
    window.update()
    while time.time() < end:
        window.update()
        time.sleep(0.005)


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def find_text(widget, text, kind=None):
    for child in descendants(widget):
        try:
            if child.cget("text") == text and (kind is None or isinstance(child, kind)):
                return child
        except tk.TclError:
            continue
    raise AssertionError(f"no widget with text {text!r}")


def send(widget, sequence):
    """Send a keyboard event to a widget (tkinter only delivers key events to the widget that has focus)."""
    widget.focus_force()
    widget.update()
    widget.event_generate(sequence)


def press(window, text, key=None):
    """Click one of a Popup's flat text buttons (Labels showing the text in capitals), or send a key to the popup card.

    Meant to be run from window.after(): the popup may not be on screen yet (slower on Windows), so it waits until it
    is, and if it never appears or never reacts it closes the card so a test fails instead of hanging.
    """
    def attempt(tries=0):
        try:
            label = find_text(window, text.upper() if key is None else text, tk.Label)
        except AssertionError:
            return  # popup already closed
        if not label.winfo_viewable() and tries < 200:
            window.after(25, attempt, tries + 1)
            return
        if tries >= 200:  # never became visible: close the card so the test cannot hang
            holder = label
            while holder.master is not window:
                holder = holder.master
            holder.destroy()
            return
        if key is None:
            label.event_generate("<Button-1>", x=1, y=1)
        else:
            holder = label
            while holder.master is not window:
                holder = holder.master
            holder.focus_force()
            holder.update()
            holder.event_generate(key)
        window.after(1000, lambda: giveup(label))  # still open a second after our click: close it, the test will fail

    def giveup(label):
        try:
            holder = label
            while holder.master is not window:
                holder = holder.master
            holder.destroy()
        except tk.TclError:
            pass

    attempt()


class GuiTestCase(unittest.TestCase):
    """Builds the real app window with a fake IOManager and engine, so no AI, files or network are touched."""

    def setUp(self):
        self.engine = mock.Mock()
        self.engine.profile = make_profile()
        self.io = mock.Mock()
        self.io.profile = self.engine.profile
        self.io.check_field.return_value = FieldCheck()
        self.io.trend_chart.return_value = ChartResult(default="trend text")
        self.io.weekly_chart.return_value = ChartResult(default="weekly text")
        patcher = mock.patch("gui.app.IOManager", return_value=self.io)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.app = SmartBiteApp(self.engine)
        self.addCleanup(self.app.destroy)
        self.app.run_in_background = lambda work, on_done: on_done(work())  # no threads: run the work straight away
        pump(self.app)

    def screen(self, name):
        return self.app._screens[name]

    def type_into(self, entry, text):
        entry.delete(0, "end")
        entry.insert(0, text)


# =========== Popups ===========
class PopupTests(GuiTestCase):
    def ask(self, buttons, action):
        self.app.after(50, action)
        return popups.Popup(self.app, "Title", "Message", buttons=buttons)

    def test_center_on_screen_moves_the_window_to_the_middle(self):
        window = tk.Toplevel(self.app)
        self.addCleanup(window.destroy)
        window.geometry("200x100")
        popups.center_on_screen(window)
        window.update()
        self.assertEqual(window.winfo_x(), (window.winfo_screenwidth() - 200) // 2)

    def test_clicking_a_button_returns_that_answer_and_removes_the_card(self):
        popup = self.ask(("OK",), lambda: press(self.app, "OK"))
        self.assertEqual(popup.answer, "OK")
        with self.assertRaises(AssertionError):
            find_text(self.app, "Title", tk.Label)

    def test_the_clicked_button_of_several_is_the_answer(self):
        self.assertEqual(self.ask(("No", "Yes"), lambda: press(self.app, "Yes")).answer, "Yes")

    def test_escape_closes_with_no_answer_and_enter_picks_the_first_button(self):
        self.assertIsNone(self.ask(("No", "Yes"), lambda: press(self.app, "Title", key="<Escape>")).answer)
        self.assertEqual(self.ask(("No", "Yes"), lambda: press(self.app, "Title", key="<Return>")).answer, "No")

    def test_ask_yes_no_is_true_only_for_yes(self):
        self.app.after(50, lambda: press(self.app, "Yes"))
        self.assertIs(popups.ask_yes_no("Sure?", "Really?", self.app), True)
        self.app.after(50, lambda: press(self.app, "No"))
        self.assertIs(popups.ask_yes_no("Sure?", "Really?", self.app), False)

    def test_show_error_uses_the_errors_own_title_and_description(self):
        with mock.patch("gui.popups.Popup") as popup:
            popups.show_error(DataError("File broken"), self.app)
        popup.assert_called_once_with(self.app, "Data Error", "File broken")

    def test_show_error_hides_details_of_unplanned_errors(self):
        with mock.patch("gui.popups.Popup") as popup:
            popups.show_error(RuntimeError("secret internals"), self.app)
        _parent, title, message = popup.call_args.args
        self.assertEqual((title, message), (UnexpectedError.title, UnexpectedError().description))


# =========== Hint label next to a field ===========
class HintLabelTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.accepted = []
        self.hint = HintLabel(self.app, on_accept=self.accepted.append)
        self.hint.pack()

    def test_a_problem_is_red_plain_and_cannot_be_accepted(self):
        self.hint.show(FieldCheck("Username taken"))
        self.assertEqual(str(self.hint.cget("text")), "Username taken")
        self.assertEqual(str(self.hint.cget("foreground")), PROBLEM_COLOUR)
        self.hint.event_generate("<Button-1>")
        self.assertEqual(self.accepted, [])

    def test_a_suggestion_is_blue_and_clicking_it_accepts_the_fix(self):
        self.hint.show(FieldCheck("Did you mean Singapore?", fix="Singapore"))
        self.assertEqual(str(self.hint.cget("foreground")), SUGGESTION_COLOUR)
        self.assertEqual(str(self.hint.cget("cursor")), "hand2")
        self.hint.event_generate("<Button-1>")
        self.assertEqual(self.accepted, ["Singapore"])

    def test_clear_removes_the_message_and_the_fix(self):
        self.hint.show(FieldCheck("Did you mean Singapore?", fix="Singapore"))
        self.hint.clear()
        self.hint.event_generate("<Button-1>")
        self.assertEqual(str(self.hint.cget("text")), "")
        self.assertEqual(self.accepted, [])

    def test_checking_waits_until_typing_stops_and_runs_once(self):
        entry, check = tk.Entry(self.app), mock.Mock()
        entry.pack()
        with mock.patch("gui.hint_label.TYPING_PAUSE_MS", 40):
            self.hint.watch(entry, check)
            for _ in range(3):
                send(entry, "<KeyRelease>")
            pump(self.app, 0.02)
            check.assert_not_called()
            pump(self.app, 0.15)
        check.assert_called_once()

    def test_leaving_the_field_checks_straight_away_and_cancels_the_wait(self):
        entry, check = tk.Entry(self.app), mock.Mock()
        entry.pack()
        with mock.patch("gui.hint_label.TYPING_PAUSE_MS", 40):
            self.hint.watch(entry, check)
            send(entry, "<KeyRelease>")
            send(entry, "<FocusOut>")
            check.assert_called_once()
            pump(self.app, 0.15)
        check.assert_called_once()


# =========== Window and navigation ===========
class AppTests(GuiTestCase):
    def test_every_screen_is_created(self):
        self.assertEqual(set(self.app._screens), {"login", "register", "home", "dashboard", "profile"})

    def test_show_raises_the_screen_and_lets_it_refresh_first(self):
        home = self.screen("home")
        calls = mock.Mock()
        home.tkraise, home.on_show = calls.raise_, calls.refresh
        self.app.show("home")
        self.assertEqual([call[0] for call in calls.mock_calls], ["refresh", "raise_"])

    def test_showing_an_unknown_screen_fails(self):
        with self.assertRaises(KeyError):
            self.app.show("nowhere")

    def test_logout_logs_out_and_returns_to_the_login_screen(self):
        with mock.patch.object(self.app, "show") as show:
            self.app.logout()
        self.io.logout.assert_called_once_with()
        show.assert_called_once_with("login")


class BackgroundWorkTests(GuiTestCase):
    """The real run_in_background (the other tests replace it with a straight call)."""

    def setUp(self):
        super().setUp()
        del self.app.run_in_background  # back to the real method

    def wait_for(self, done):
        end = time.time() + 3
        while not done and time.time() < end:
            pump(self.app, 0.02)

    def test_the_result_comes_back_to_on_done(self):
        done = []
        self.app.run_in_background(lambda: 42, done.append)
        self.wait_for(done)
        self.assertEqual(done, [42])

    def test_a_failure_shows_an_error_popup_and_gives_none(self):
        done, problem = [], DataError("disk")
        with mock.patch("gui.app.show_error") as show_error:
            self.app.run_in_background(lambda: (_ for _ in ()).throw(problem), done.append)
            self.wait_for(done)
        self.assertEqual(done, [None])
        show_error.assert_called_once_with(problem, self.app)


# =========== Login screen ===========
class LoginFrameTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.login = self.screen("login")
        self.type_into(self.login.username, "jane")
        self.type_into(self.login.password, "secret")

    def test_the_password_is_hidden_while_typing(self):
        self.assertEqual(str(self.login.password.cget("show")), "•")

    def test_log_in_sends_the_typed_details_and_opens_home(self):
        with mock.patch.object(self.app, "show") as show:
            find_text(self.login, "Log in", tk.Widget).invoke()
        self.io.login.assert_called_once_with("jane", "secret")
        show.assert_called_once_with("home")

    def test_enter_in_the_password_box_also_logs_in(self):
        send(self.login.password, "<Return>")
        self.io.login.assert_called_once_with("jane", "secret")

    def test_a_failed_login_shows_the_error_and_stays_on_the_screen(self):
        self.io.login.side_effect = LoginFailedError()
        with mock.patch("gui.login_frame.show_error") as show_error, mock.patch.object(self.app, "show") as show:
            self.login._login()
        show_error.assert_called_once()
        show.assert_not_called()

    def test_opening_the_screen_clears_the_password_only(self):
        self.login.on_show()
        self.assertEqual(self.login.password.get(), "")
        self.assertEqual(self.login.username.get(), "jane")

    def test_create_an_account_opens_the_register_screen(self):
        with mock.patch.object(self.app, "show") as show:
            find_text(self.login, "Create an account", tk.Widget).invoke()
        show.assert_called_once_with("register")


# =========== Register screen ===========
class RegisterFrameTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.register = self.screen("register")

    def fill(self):
        for key, value in {"username": "jane", "password": "pw", "age": "30", "height": "165", "weight": "55",
                           "country": "Singapore", "ethnicity": "Chinese", "conditions": "asthma"}.items():
            self.type_into(self.register.fields[key], value)
        self.register.fields["gender"].set("female")

    def test_the_form_has_every_field_and_hides_the_password(self):
        self.assertEqual(set(self.register.fields), {"username", "password", "gender", "age", "height", "weight",
                                                     "country", "ethnicity", "conditions"})
        self.assertEqual(str(self.register.fields["password"].cget("show")), "•")

    def test_gender_can_only_be_picked_from_the_list(self):
        gender = self.register.fields["gender"]
        self.assertEqual(str(gender.cget("state")), "readonly")
        self.assertEqual(list(gender.cget("values")), ["male", "female"])

    def test_only_the_four_live_fields_get_hints(self):
        self.assertEqual(set(self.register.hints), {"username", "country", "ethnicity", "conditions"})

    def test_create_account_sends_the_raw_text_and_opens_home(self):
        self.fill()
        with mock.patch.object(self.app, "show") as show:
            self.register._register()
        form = self.io.register.call_args.args[0]
        self.assertEqual((form["username"], form["age"], form["gender"], form["conditions"]), ("jane", "30", "female", "asthma"))
        show.assert_called_once_with("home")

    def test_a_rejected_form_shows_the_error_and_stays(self):
        self.io.register.side_effect = DataError()
        with mock.patch("gui.register_frame.show_error") as show_error, mock.patch.object(self.app, "show") as show:
            self.register._register()
        show_error.assert_called_once()
        show.assert_not_called()

    def test_opening_the_screen_clears_every_field_and_hint(self):
        self.fill()
        self.register.hints["country"].show(FieldCheck("Not a recognised country"))
        self.register.on_show()
        self.assertTrue(all(widget.get() == "" for widget in self.register.fields.values()))
        self.assertEqual(str(self.register.hints["country"].cget("text")), "")

    def test_a_live_check_shows_its_result_in_the_hint(self):
        self.io.check_field.return_value = FieldCheck("Username taken")
        self.type_into(self.register.fields["username"], "jane")
        self.register._check_field("username")
        self.io.check_field.assert_called_once_with("username", "jane")
        self.assertEqual(str(self.register.hints["username"].cget("text")), "Username taken")

    def test_accepting_a_suggestion_fills_the_field_and_checks_it_again(self):
        self.type_into(self.register.fields["country"], "Singapor")
        self.register._accept_fix("country", "Singapore")
        self.assertEqual(self.register.fields["country"].get(), "Singapore")
        self.io.check_field.assert_called_with("country", "Singapore")

    def test_back_to_login_button(self):
        with mock.patch.object(self.app, "show") as show:
            find_text(self.register, "Back to login", tk.Widget).invoke()
        show.assert_called_once_with("login")


# =========== Follow-up questions dialog ===========
class QuestionsDialogTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.dialog = QuestionsDialog(self.app, ["How big was the bowl?", "Any sauce?"])
        self.addCleanup(lambda: self.dialog.winfo_exists() and self.dialog.destroy())

    def test_there_is_one_answer_box_per_question(self):
        self.assertEqual(list(self.dialog._entries), ["How big was the bowl?", "Any sauce?"])

    def test_submit_gives_the_answers_by_question_and_closes(self):
        self.type_into(self.dialog._entries["How big was the bowl?"], "Large")
        self.type_into(self.dialog._entries["Any sauce?"], "No")
        find_text(self.dialog, "Submit", tk.Widget).invoke()
        self.assertEqual(self.dialog.answers, {"How big was the bowl?": "Large", "Any sauce?": "No"})
        self.assertFalse(self.dialog.winfo_exists())

    def test_cancel_check_closes_with_no_answers(self):
        find_text(self.dialog, "Cancel check", tk.Widget).invoke()
        self.assertIsNone(self.dialog.answers)
        self.assertFalse(self.dialog.winfo_exists())


# =========== Home screen (food check) ===========
class HomeFrameTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.home = self.screen("home")
        self.home.on_show()

    def check(self, food="Salty Crackers", barcode=""):
        self.type_into(self.home.food, food)
        self.type_into(self.home.barcode, barcode)
        self.home._start_check()

    def test_opening_the_screen_greets_the_user_and_clears_the_last_check(self):
        self.type_into(self.home.food, "Old food")
        self.engine.check_food.return_value = step(assessment_outcome())
        self.home._start_check()
        self.home.on_show()
        self.assertEqual(str(self.home.welcome.cget("text")), "Hi, jane")
        self.assertEqual((self.home.food.get(), self.home.barcode.get()), ("", ""))
        self.assertFalse(self.home.verdict.winfo_manager())
        self.assertFalse(self.home.result.winfo_manager())

    def test_no_greeting_when_nobody_is_logged_in(self):
        self.engine.profile = None
        self.home.on_show()
        self.assertEqual(str(self.home.welcome.cget("text")), "")

    def test_check_sends_food_and_barcode_to_the_engine(self):
        self.engine.check_food.return_value = step(assessment_outcome())
        self.check("Crackers", "12345678")
        self.engine.check_food.assert_called_once_with("Crackers", "12345678")

    def test_buttons_are_locked_while_checking_and_unlocked_after(self):
        states = []

        def work():
            states.append([str(b.cget("state")) for b in [self.home.check_button, *self.home.nav_buttons]])
            return step(assessment_outcome())

        self.app.run_in_background = lambda w, on_done: on_done(work())
        self.engine.check_food.side_effect = lambda *_: work()
        self.check()
        self.assertEqual(set(states[0]), {"disabled"})
        self.assertEqual(str(self.home.check_button.cget("state")), "normal")
        self.assertEqual(str(self.home.status.cget("text")), "")

    def test_a_failed_check_unlocks_the_screen_and_shows_no_result(self):
        self.app.run_in_background = lambda work, on_done: on_done(None)  # run_in_background gives None after an error popup
        self.check()
        self.assertEqual(str(self.home.check_button.cget("state")), "normal")
        self.assertFalse(self.home.verdict.winfo_manager())

    def test_the_verdict_banner_has_the_headline_meaning_and_colour(self):
        self.engine.check_food.return_value = step(assessment_outcome("CAUTION"))
        self.check()
        self.assertEqual(str(self.home.verdict.cget("text")), "CAUTION – Eat with caution")
        self.assertEqual(str(self.home.verdict.cget("bg")), VERDICT_COLOURS["CAUTION"])

    def test_the_result_lists_reason_allergens_flags_nutrients_and_confidence(self):
        self.engine.check_food.return_value = step(assessment_outcome())
        self.check()
        text = self.home.result.get("1.0", "end")
        for expected in ("Very salty.", "tree nuts: almond", "sodium_mg: 900 (high)", "Nutrients per 100 g", "AI confidence: 8/10"):
            self.assertIn(expected, text)

    def test_sections_with_nothing_to_show_are_left_out(self):
        self.engine.check_food.return_value = step(assessment_outcome("OK", flags=[], allergens_found={}, nutrients={}))
        self.check()
        text = self.home.result.get("1.0", "end")
        for missing in ("Allergens found", "Flagged nutrients", "Nutrients per"):
            self.assertNotIn(missing, text)

    def test_the_fallback_shows_the_message_and_recommendations_in_grey(self):
        self.engine.check_food.return_value = step(fallback_outcome())
        self.check()
        self.assertEqual(str(self.home.verdict.cget("bg")), VERDICT_COLOURS["UNDETERMINED"])
        text = self.home.result.get("1.0", "end")
        self.assertIn("We cannot decide.", text)
        self.assertIn("Apple: Light and sweet.", text)

    def test_the_result_box_is_read_only(self):
        self.engine.check_food.return_value = step(assessment_outcome())
        self.check()
        self.assertEqual(str(self.home.result.cget("state")), "disabled")

    def test_follow_up_answers_are_sent_back_to_the_engine(self):
        self.engine.check_food.return_value = step(questions=["Size?"])
        self.engine.answer_questions.return_value = step(assessment_outcome("OK"))
        with mock.patch("gui.home_frame.QuestionsDialog") as dialog:
            dialog.return_value.answers = {"Size?": "Large"}
            with mock.patch.object(self.home, "wait_window"):
                self.check()
        dialog.assert_called_once_with(self.home, ["Size?"])
        self.engine.answer_questions.assert_called_once_with({"Size?": "Large"})
        self.assertIn("OK", str(self.home.verdict.cget("text")))

    def test_cancelling_the_questions_cancels_the_check(self):
        self.engine.check_food.return_value = step(questions=["Size?"])
        with mock.patch("gui.home_frame.QuestionsDialog") as dialog:
            dialog.return_value.answers = None
            with mock.patch.object(self.home, "wait_window"):
                self.check()
        self.engine.cancel_food_check.assert_called_once_with()
        self.engine.answer_questions.assert_not_called()
        self.assertEqual(str(self.home.status.cget("text")), "Check cancelled.")

    def test_navigation_buttons_go_to_progress_and_profile(self):
        with mock.patch.object(self.app, "show") as show:
            find_text(self.home, "My progress", tk.Widget).invoke()
            find_text(self.home, "My profile", tk.Widget).invoke()
        self.assertEqual([call.args[0] for call in show.call_args_list], ["dashboard", "profile"])


# =========== Dashboard (where the graphs are shown) ===========
class DashboardFrameTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.dashboard = self.screen("dashboard")

    def test_there_is_a_tab_for_each_chart(self):
        self.assertEqual([self.dashboard.tabs.tab(i, "text") for i in range(2)], ["Trend", "Weekly"])

    def test_a_chart_without_a_graph_shows_its_text_instead(self):
        self.dashboard.on_show()
        self.assertEqual(find_text(self.dashboard.trend_tab, "trend text").winfo_class(), "TLabel")
        self.assertEqual(find_text(self.dashboard.weekly_tab, "weekly text").winfo_class(), "TLabel")

    def test_a_chart_with_a_graph_is_drawn_on_a_canvas(self):
        self.io.trend_chart.return_value = ChartResult(graph=Figure())
        self.dashboard.on_show()
        classes = [child.winfo_class() for child in self.dashboard.trend_tab.winfo_children()]
        self.assertEqual(classes, ["Canvas"])

    def test_every_visit_redraws_instead_of_stacking_old_charts(self):
        self.dashboard.on_show()
        self.io.trend_chart.return_value = ChartResult(graph=Figure())
        self.dashboard.on_show()
        self.dashboard.on_show()
        self.assertEqual(len(self.dashboard.trend_tab.winfo_children()), 1)
        self.assertEqual(self.io.trend_chart.call_count, 3)

    def test_back_button_returns_home(self):
        with mock.patch.object(self.app, "show") as show:
            find_text(self.dashboard, "Back", tk.Widget).invoke()
        show.assert_called_once_with("home")


# =========== Profile screen ===========
class ProfileFrameTests(GuiTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.screen("profile")
        self.profile.on_show()

    def ticks(self):
        return [child for child in self.profile.ticks_box.winfo_children() if child.winfo_class() == "TCheckbutton"]

    def test_the_screen_is_filled_in_from_the_profile(self):
        self.assertIn("jane", str(self.profile.fixed.cget("text")))
        self.assertEqual({key: entry.get() for key, entry in self.profile.fields.items()},
                         {"age": "30", "height": "165.0", "weight": "55.0", "country": "Singapore"})
        self.assertEqual([tick.cget("text") for tick in self.ticks()], ["Asthma", "Peanut Allergy"])

    def test_nothing_happens_when_nobody_is_logged_in(self):
        self.io.profile = None
        self.type_into(self.profile.fields["age"], "99")
        self.profile.on_show()
        self.assertEqual(self.profile.fields["age"].get(), "99")

    def test_no_conditions_shows_a_placeholder(self):
        self.io.profile = make_profile(medical_conditions=[])
        self.profile.on_show()
        self.assertEqual(self.ticks(), [])
        find_text(self.profile.ticks_box, "None added yet.")

    def test_save_changes_sends_the_edited_form_and_confirms(self):
        self.type_into(self.profile.fields["age"], "31")
        with mock.patch("gui.profile_frame.show_info") as show_info:
            self.profile._save_details()
        self.io.update_profile.assert_called_once_with({"age": "31", "height": "165.0", "weight": "55.0", "country": "Singapore"})
        show_info.assert_called_once()

    def test_a_rejected_edit_shows_the_error_and_no_confirmation(self):
        self.io.update_profile.side_effect = DataError()
        with mock.patch("gui.profile_frame.show_error") as show_error, mock.patch("gui.profile_frame.show_info") as show_info:
            self.profile._save_details()
        show_error.assert_called_once()
        show_info.assert_not_called()

    def test_removing_sends_the_positions_of_the_ticked_conditions(self):
        self.ticks()[1].invoke()
        self.profile._remove_conditions()
        self.io.remove_conditions.assert_called_once_with([1])

    def test_adding_sends_the_typed_text(self):
        self.type_into(self.profile.new_conditions, "diabetes")
        self.profile._add_conditions()
        self.io.add_conditions.assert_called_once_with("diabetes")

    def test_a_rejected_add_shows_the_error(self):
        self.io.add_conditions.side_effect = DataError()
        with mock.patch("gui.profile_frame.show_error") as show_error:
            self.profile._add_conditions()
        show_error.assert_called_once()

    def test_a_country_suggestion_fills_the_field_and_is_checked_again(self):
        self.profile._accept_country("Malaysia")
        self.assertEqual(self.profile.fields["country"].get(), "Malaysia")
        self.io.check_field.assert_called_with("country", "Malaysia")

    def test_deleting_needs_a_yes_and_then_returns_to_login(self):
        with mock.patch("gui.profile_frame.ask_yes_no", return_value=True), \
                mock.patch("gui.profile_frame.show_info") as show_info, mock.patch.object(self.app, "show") as show:
            self.profile._delete_account()
        self.io.delete_account.assert_called_once_with()
        show_info.assert_called_once()
        show.assert_called_once_with("login")

    def test_saying_no_keeps_the_account(self):
        with mock.patch("gui.profile_frame.ask_yes_no", return_value=False), mock.patch.object(self.app, "show") as show:
            self.profile._delete_account()
        self.io.delete_account.assert_not_called()
        show.assert_not_called()

    def test_a_failed_delete_shows_the_error_and_stays(self):
        self.io.delete_account.side_effect = DataError()
        with mock.patch("gui.profile_frame.ask_yes_no", return_value=True), mock.patch("gui.profile_frame.show_error") as show_error, \
                mock.patch.object(self.app, "show") as show:
            self.profile._delete_account()
        show_error.assert_called_once()
        show.assert_not_called()


if __name__ == "__main__":
    unittest.main()