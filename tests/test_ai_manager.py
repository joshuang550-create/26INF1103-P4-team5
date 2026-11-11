"""AIManager: prompt building, retrying on malformed output, fallback and chat history."""
import unittest

from managers.ai_manager import AIManager, PromptBuilder
from models.errors import AIConnectionError, AIResponseError
from tests.helpers import FakeModel, TempDataTestCase, ai_reply, fallback_reply, make_profile, sample_product


class PromptBuilderTests(unittest.TestCase):
    def test_food_prompt_contains_profile_and_food(self):
        prompt = PromptBuilder.check_food_prompt(make_profile(["hypertension"]), "Chicken rice")
        for expected in ("Chicken rice", "hypertension", "Singapore", "30"):
            self.assertIn(expected, prompt)
        self.assertNotIn("OPEN FOOD FACTS DATA", prompt)

    def test_food_prompt_without_conditions_says_none_reported(self):
        self.assertIn("none reported", PromptBuilder.check_food_prompt(make_profile(), "Apple"))

    def test_food_prompt_includes_barcode_product_data(self):
        prompt = PromptBuilder.check_food_prompt(make_profile(), "Crackers", sample_product())
        for expected in ("OPEN FOOD FACTS DATA", "Salty Crackers", "12345678", "wheat flour"):
            self.assertIn(expected, prompt)

    def test_follow_up_prompt_lists_every_question_and_answer(self):
        prompt = PromptBuilder.check_food_follow_up_prompt({"Which kind?": "carrot", "How much?": "one slice"})
        for expected in ("Q: Which kind?", "A: carrot", "Q: How much?", "A: one slice"):
            self.assertIn(expected, prompt)

    def test_invalid_prompt_lists_each_issue_once(self):
        prompt = PromptBuilder.invalid_response_prompt(["invalid_reason", "invalid_reason", "invalid_json"])
        self.assertEqual(prompt.count("reason must be a non-empty string"), 1)
        self.assertIn("not valid JSON", prompt)

    def test_unknown_issue_gets_generic_message(self):
        self.assertIn("did not match the required format", PromptBuilder.invalid_response_prompt(["made_up_issue"]))

    def test_special_prompts_have_their_trigger_words(self):
        self.assertIn("REASSESS", PromptBuilder.low_confidence_reprompt())
        self.assertIn("FALLBACK REQUEST", PromptBuilder.fallback_prompt(make_profile()))

    def test_system_instruction_describes_expected_json_keys(self):
        for key in ("information_needed", "confidence_score", "potential_concern", "sodium_mg"):
            self.assertIn(key, PromptBuilder().system_instruction)


class AIManagerTests(TempDataTestCase):
    def make_manager(self, replies):
        self.model = FakeModel(replies)
        return AIManager(self.data, self.model)

    def test_valid_reply_returns_assessment(self):
        result = self.make_manager([ai_reply(confidence=80)]).check_food(make_profile(), "Apple")
        self.assertEqual(result.confidence, 8.0)
        self.assertEqual(len(self.model.prompts), 1)

    def test_malformed_reply_is_retried_with_a_correction_prompt(self):
        manager = self.make_manager(["this is not json", ai_reply()])
        result = manager.check_food(make_profile(), "Apple")
        self.assertIsNotNone(result)
        self.assertEqual(len(self.model.prompts), 2)
        self.assertIn("INVALID REPLY", self.model.prompts[1])
        self.assertIn("not valid JSON", self.model.prompts[1])

    def test_gives_up_after_two_malformed_replies(self):
        manager = self.make_manager(["nope", '{"still": "wrong"}'])
        with self.assertRaises(AIResponseError):
            manager.check_food(make_profile(), "Apple")
        self.assertEqual(len(self.model.prompts), 2)  # no endless loop

    def test_follow_up_and_reprompt_use_the_right_messages(self):
        manager = self.make_manager([ai_reply(), ai_reply()])
        manager.follow_up(make_profile(), {"Which kind?": "carrot"})
        manager.reprompt(make_profile())
        self.assertIn("ANSWERS TO YOUR QUESTIONS", self.model.prompts[0])
        self.assertIn("REASSESS", self.model.prompts[1])

    def test_fallback_returns_recommendations(self):
        result = self.make_manager([fallback_reply(4)]).fallback(make_profile())
        self.assertEqual(len(result), 4)

    def test_fallback_recovers_from_one_bad_reply(self):
        result = self.make_manager(["garbage", fallback_reply()]).fallback(make_profile())
        self.assertEqual(len(result), 3)

    def test_fallback_gives_up_after_retries(self):
        with self.assertRaises(AIResponseError):
            self.make_manager(["garbage", "more garbage"]).fallback(make_profile())

    def test_model_errors_are_not_swallowed(self):
        with self.assertRaises(AIConnectionError):
            self.make_manager([AIConnectionError()]).check_food(make_profile(), "Apple")

    def test_conversation_is_saved_per_user(self):
        self.make_manager([ai_reply()]).check_food(make_profile(), "Apple")
        history = self.data.get_chat_history("tester")
        self.assertEqual([item["role"] for item in history], ["user", "model"])
        self.assertIsNone(self.data.get_chat_history("someone_else"))

    def test_saved_history_is_sent_with_the_next_request(self):
        manager = self.make_manager([ai_reply(), ai_reply()])
        manager.check_food(make_profile(), "Apple")
        sent = []
        original_send = self.model.send
        self.model.send = lambda prompt, history, system: (sent.append(len(history)), original_send(prompt, history, system))[1]
        manager.check_food(make_profile(), "Banana")
        self.assertEqual(sent, [2])  # the earlier user + model messages


if __name__ == "__main__":
    unittest.main()
