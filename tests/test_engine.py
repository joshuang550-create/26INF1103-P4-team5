"""End-to-end behaviour of AppEngine (the facade the GUI uses) with a scripted fake AI."""
from exceptions.ai_connection_error import AIConnectionError
from exceptions.ai_response_error import AIResponseError
from exceptions.invalid_action_error import InvalidActionError
from exceptions.invalid_input_error import InvalidInputError
from exceptions.login_failed_error import LoginFailedError

from services.openfoodfacts.food_lookup_error import FoodLookupError
from logic.outcomes.recommendation_outcome import RecommendationOutcome
from logic.verdict import Verdict

from tests.helpers import FakeSearcher, TempDataTestCase, ai_reply, fallback_reply, sample_product
import json


class FoodCheckVerdictTests(TempDataTestCase):
    """The business rules: severity -> verdict, allergens override severity."""

    def check(self, reply, conditions=None, food="Test food"):
        engine = self.make_engine([reply], conditions=conditions)
        step = engine.check_food(food)
        self.assertFalse(step.needs_answers)
        return step.outcome

    def test_safe_food_is_ok(self):
        outcome = self.check(ai_reply())
        self.assertEqual((outcome.headline, outcome.severity), ("OK", Verdict.OK))

    def test_high_nutrient_for_relevant_condition_is_avoid(self):
        outcome = self.check(ai_reply(sodium_mg=700), ["hypertension"])
        self.assertEqual(outcome.headline, "AVOID")
        self.assertEqual(outcome.details()["flags"][0], {"nutrient": "sodium_mg", "value": 700, "level": "high"})

    def test_moderate_nutrient_is_caution(self):
        self.assertEqual(self.check(ai_reply(sodium_mg=400), ["hypertension"]).headline, "CAUTION")

    def test_same_food_is_ok_for_user_without_the_condition(self):
        self.assertEqual(self.check(ai_reply(sodium_mg=700)).headline, "OK")

    def test_ai_concern_alone_is_caution(self):
        self.assertEqual(self.check(ai_reply(concern=True)).headline, "CAUTION")

    def test_allergen_overrides_everything_and_skips_reprompt(self):
        # confidence is very low, but an allergen must still give AVOID straight away (FakeModel has only one reply)
        outcome = self.check(ai_reply(reason="Made with fresh shrimp.", confidence=5), ["shrimp allergy"])
        self.assertEqual(outcome.headline, "AVOID")
        self.assertIn("shellfish_crustacean", outcome.details()["allergens_found"])

    def test_allergen_the_user_does_not_have_is_ignored(self):
        self.assertEqual(self.check(ai_reply(reason="Made with fresh shrimp."), ["asthma"]).headline, "OK")

    def test_outcome_dict_is_ready_for_the_gui(self):
        data = self.check(ai_reply(sodium_mg=700), ["hypertension"]).to_dict()
        self.assertEqual({"headline", "severity", "details"}, set(data))
        self.assertEqual(data["severity"], "AVOID")


class ConfidenceRoutingTests(TempDataTestCase):
    def test_low_confidence_is_reprompted_then_accepted(self):
        engine = self.make_engine([ai_reply(confidence=20), ai_reply(confidence=85)])
        outcome = engine.check_food("Mystery stew").outcome
        self.assertEqual(outcome.headline, "OK")
        self.assertEqual(len(self.model.prompts), 2)
        self.assertIn("REASSESS", self.model.prompts[1])

    def test_still_low_after_reprompt_gives_recommendations(self):
        engine = self.make_engine([ai_reply(confidence=20), ai_reply(confidence=30), fallback_reply(3)])
        outcome = engine.check_food("Mystery stew").outcome
        self.assertIsInstance(outcome, RecommendationOutcome)
        self.assertEqual(outcome.headline, "UNDETERMINED")
        self.assertEqual(len(outcome.details()["recommendations"]), 3)
        self.assertIn("FALLBACK REQUEST", self.model.prompts[2])

    def test_state_is_reset_after_a_finished_check(self):
        engine = self.make_engine([ai_reply(confidence=20), ai_reply(confidence=30), fallback_reply(), ai_reply()])
        engine.check_food("Mystery stew")
        self.assertEqual(engine.check_food("Apple").outcome.headline, "OK")  # fresh attempt counter, no leftovers


class FollowUpQuestionTests(TempDataTestCase):
    QUESTION = "Which kind of cake is it? (e.g. carrot, sponge)"

    def test_questions_then_answers_then_outcome(self):
        engine = self.make_engine([ai_reply(questions=[self.QUESTION]), ai_reply()])
        step = engine.check_food("Cake")
        self.assertTrue(step.needs_answers)
        self.assertEqual(step.questions, (self.QUESTION,))
        self.assertIsNone(step.outcome)

        final = engine.answer_questions({self.QUESTION: "  carrot  "})
        self.assertFalse(final.needs_answers)
        self.assertEqual(final.outcome.headline, "OK")
        self.assertIn("A: carrot", self.model.prompts[1])  # answer was trimmed and sent

    def test_every_question_must_be_answered(self):
        engine = self.make_engine([ai_reply(questions=["Q1?", "Q2?"])])
        engine.check_food("Cake")
        for bad in ({"Q1?": "a"}, {"Q1?": "a", "Q2?": "   "}, {"Q1?": "a", "Q2?": 5}, "not a dict", None):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                engine.answer_questions(bad)

    def test_answers_without_a_pending_check_are_refused(self):
        engine = self.make_engine([])
        with self.assertRaises(InvalidActionError):
            engine.answer_questions({"Q?": "a"})

    def test_cancel_ends_the_pending_check(self):
        engine = self.make_engine([ai_reply(questions=["Q?"])])
        engine.check_food("Cake")
        engine.cancel_food_check()
        with self.assertRaises(InvalidActionError):
            engine.answer_questions({"Q?": "a"})

    def test_runaway_follow_up_questions_are_stopped(self):
        engine = self.make_engine([ai_reply(questions=["Q?"])] * 3)
        engine.check_food("Cake")                      # round 1 of questions
        engine.answer_questions({"Q?": "a"})           # round 2 of questions
        with self.assertRaises(AIResponseError):       # round 3 is refused
            engine.answer_questions({"Q?": "a"})
        with self.assertRaises(InvalidActionError):    # and the check was reset
            engine.answer_questions({"Q?": "a"})


class MalformedAIOutputTests(TempDataTestCase):
    def test_recovers_when_ai_corrects_itself(self):
        engine = self.make_engine(["I think it is fine!", ai_reply()])
        self.assertEqual(engine.check_food("Apple").outcome.headline, "OK")

    def test_raises_clear_error_when_ai_keeps_failing(self):
        engine = self.make_engine(["nope", json.dumps({"reason": "x"})])
        with self.assertRaises(AIResponseError):
            engine.check_food("Apple")

    def test_ai_service_errors_reach_the_caller(self):
        engine = self.make_engine([AIConnectionError()])
        with self.assertRaises(AIConnectionError):
            engine.check_food("Apple")


class InputValidationTests(TempDataTestCase):
    def test_login_required_for_food_check(self):
        engine = self.make_engine([], login=False)
        with self.assertRaises(InvalidActionError):
            engine.check_food("Apple")

    def test_food_name_must_be_meaningful(self):
        engine = self.make_engine([])
        for bad in ("", " ", "a", None, 5):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                engine.check_food(bad)
        self.assertEqual(self.model.prompts, [])  # AI never called

    def test_bad_barcode_is_rejected_before_calling_the_ai(self):
        engine = self.make_engine([])
        for bad in ("123", "abcdefgh", "123456789"):
            with self.assertRaises(InvalidInputError, msg=bad):
                engine.check_food("Crackers", bad)
        self.assertEqual((self.model.prompts, self.searcher.calls), ([], []))

    def test_valid_barcode_adds_product_data_to_prompt(self):
        engine = self.make_engine([ai_reply()], searcher=FakeSearcher(product=sample_product()))
        engine.check_food("Crackers", "12345678")
        self.assertEqual(self.searcher.calls, ["12345678"])
        self.assertIn("Salty Crackers", self.model.prompts[0])

    def test_unknown_barcode_continues_without_product_data(self):
        engine = self.make_engine([ai_reply()], searcher=FakeSearcher(product=None))
        self.assertEqual(engine.check_food("Crackers", "12345678").outcome.headline, "OK")
        self.assertNotIn("OPEN FOOD FACTS DATA", self.model.prompts[0])

    def test_barcode_lookup_failure_is_reported(self):
        engine = self.make_engine([], searcher=FakeSearcher(error=FoodLookupError()))
        with self.assertRaises(FoodLookupError):
            engine.check_food("Crackers", "12345678")
        self.assertEqual(self.model.prompts, [])

    def test_live_validation_helpers(self):
        engine = self.make_engine([], login=False)
        self.assertTrue(engine.is_valid_country(" singapore "))
        self.assertFalse(engine.is_valid_country("Atlantis"))
        self.assertTrue(engine.is_valid_ethnicity("Chinese"))
        self.assertTrue(engine.is_valid_condition("Hypertension"))
        self.assertFalse(engine.is_valid_condition("Made Up Disease"))
        self.assertTrue(engine.is_valid_barcode("12345678"))
        self.assertFalse(engine.is_valid_barcode("1234"))


class AccountTests(TempDataTestCase):
    def test_register_logs_in_and_saves_hashed_password(self):
        engine = self.make_engine([], conditions=["hypertension"])
        self.assertEqual(engine.profile.username, "tester")
        with open(self.profiles_path, encoding="utf-8") as file:
            saved = json.load(file)["tester"]
        self.assertNotEqual(saved["password_hash"], "pw")  # plain password is not stored
        self.assertEqual(len(saved["password_hash"]), 64)  # a SHA-256 hex digest
        self.assertEqual(saved["medical_conditions"], ["hypertension"])

    def test_duplicate_username_is_refused_case_insensitively(self):
        engine = self.make_engine([])
        with self.assertRaises(InvalidInputError):
            engine.register("TESTER", "pw2", "male", 30, "Chinese", "Singapore", 170.0, 65.0)

    def test_register_rejects_bad_values(self):
        engine = self.make_engine([], login=False)
        args = dict(username="new", plain_password="pw", gender="male", age=30, ethnicity="Chinese", country="Singapore", height=170.0, weight=65.0)
        for field, bad in (("country", "Atlantis"), ("ethnicity", "Martian"), ("age", 0), ("plain_password", ""), ("username", "  ")):
            with self.assertRaises(InvalidInputError, msg=field):
                engine.register(**{**args, field: bad})

    def test_login_logout_and_wrong_password(self):
        engine = self.make_engine([])
        engine.logout()
        self.assertIsNone(engine.profile)
        with self.assertRaises(LoginFailedError):
            engine.login("tester", "wrong")
        with self.assertRaises(LoginFailedError):
            engine.login("nobody", "pw")
        self.assertEqual(engine.login("TESTER", "pw").username, "tester")

    def test_profile_property_returns_a_copy(self):
        engine = self.make_engine([])
        engine.profile.age = 99  # editing the copy...
        self.assertEqual(engine.profile.age, 30)  # ...does not change the real profile

    def test_delete_account_removes_profile_and_chat_history(self):
        engine = self.make_engine([ai_reply()])
        engine.check_food("Apple")
        self.assertIsNotNone(self.data.get_chat_history("tester"))
        engine.delete_account()
        self.assertFalse(self.data.is_username_taken("tester"))
        self.assertIsNone(self.data.get_chat_history("tester"))
        with self.assertRaises(InvalidActionError):
            engine.check_food("Apple")

    def test_new_account_never_inherits_old_chat_history(self):
        self.data.save_chat_history("tester", [{"role": "user", "text": "old", "time": 0}])
        self.make_engine([])
        self.assertIsNone(self.data.get_chat_history("tester"))


class ProfileEditingTests(TempDataTestCase):
    def test_edits_are_saved(self):
        engine = self.make_engine([])
        engine.update_age(31); engine.update_height(171.5); engine.update_weight(66); engine.update_country("Malaysia")
        reloaded = self.data.login("tester", "pw")
        self.assertEqual((reloaded.age, reloaded.height, reloaded.weight, reloaded.country), (31, 171.5, 66, "Malaysia"))

    def test_invalid_edit_changes_nothing(self):
        engine = self.make_engine([])
        with self.assertRaises(InvalidInputError):
            engine.update_age(500)
        with self.assertRaises(InvalidInputError):
            engine.update_country("Atlantis")
        self.assertEqual(engine.profile.age, 30)
        self.assertEqual(self.data.login("tester", "pw").age, 30)

    def test_add_and_remove_conditions(self):
        engine = self.make_engine([])
        engine.add_medical_conditions(["Hypertension", "Peanut Allergy"])
        self.assertEqual(engine.profile.medical_conditions, ["hypertension", "peanut allergy"])
        engine.remove_medical_conditions([0])
        self.assertEqual(engine.profile.medical_conditions, ["peanut allergy"])

    def test_removing_a_position_that_does_not_exist_is_refused(self):
        engine = self.make_engine([], conditions=["hypertension"])
        for bad in ([5], [-1], ["0"], [0, 1]):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                engine.remove_medical_conditions(bad)
        self.assertEqual(engine.profile.medical_conditions, ["hypertension"])

    def test_condition_changes_affect_the_next_verdict(self):
        engine = self.make_engine([ai_reply(sodium_mg=700), ai_reply(sodium_mg=700)])
        self.assertEqual(engine.check_food("Soup").outcome.headline, "OK")
        engine.add_medical_conditions(["hypertension"])
        self.assertEqual(engine.check_food("Soup").outcome.headline, "AVOID")
