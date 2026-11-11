"""Response validation: well-formed, malformed and hostile AI output."""
import json
import unittest

from managers.ai_manager import AIResponseValidator
from tests.helpers import ai_reply, fallback_reply


def good():
    return json.loads(ai_reply(confidence=90, sodium_mg=100))


class AssessmentValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = AIResponseValidator()

    def issues_for(self, data):
        return self.validator.validate(json.dumps(data) if not isinstance(data, str) else data).issues

    def test_valid_reply_gives_assessment_and_no_issues(self):
        result = self.validator.validate(ai_reply(confidence=90))
        self.assertTrue(result.ok)
        self.assertEqual(result.assessment.confidence, 9.0)  # 0-100 score becomes 0-10
        self.assertFalse(result.assessment.needs_follow_up)

    def test_valid_follow_up_request_is_accepted(self):
        result = self.validator.validate(ai_reply(questions=["Which kind?"]))
        self.assertTrue(result.ok)
        self.assertTrue(result.assessment.needs_follow_up)

    def test_dict_input_is_accepted(self):
        self.assertTrue(self.validator.validate(good()).ok)

    # ---- structure ----
    def test_not_json(self):
        self.assertEqual(self.issues_for("Sure! Here is my answer"), ("invalid_json",))

    def test_json_wrapped_in_code_fence_is_rejected(self):
        self.assertEqual(self.issues_for("```json\n" + ai_reply() + "\n```"), ("invalid_json",))

    def test_json_that_is_not_an_object(self):
        for text in ("[]", '"hello"', "42"):
            self.assertEqual(self.issues_for(text), ("invalid_structure",), text)

    def test_extra_key(self):
        data = good(); data["extra"] = 1
        self.assertIn("invalid_keys", self.issues_for(data))

    def test_missing_key(self):
        data = good(); del data["reason"]
        self.assertIn("invalid_keys", self.issues_for(data))

    # ---- information_needed ----
    def test_information_needed_must_be_list_of_non_empty_strings(self):
        for bad in ("a question", None, [""], ["ok", "  "], [1]):
            data = good(); data["information_needed"] = bad
            self.assertIn("invalid_information_needed", self.issues_for(data), repr(bad))

    # ---- portion ----
    def test_portion_must_be_a_non_negative_finite_number(self):
        for bad in (-1, "100", None, True, float("nan"), float("inf")):
            data = good(); data["portion_g"] = bad
            self.assertIn("invalid_portion", self.validator.validate(data).issues, repr(bad))

    def test_finished_assessment_needs_a_portion_above_zero(self):
        data = good(); data["portion_g"] = 0
        self.assertIn("invalid_portion", self.issues_for(data))

    # ---- nutrients ----
    def test_nutrients_must_have_exactly_the_expected_keys(self):
        data = good(); del data["nutrients"]["sodium_mg"]
        self.assertIn("invalid_nutrient", self.issues_for(data))
        data = good(); data["nutrients"]["fibre_g"] = 1
        self.assertIn("invalid_nutrient", self.issues_for(data))

    def test_nutrient_values_must_be_non_negative_plain_numbers(self):
        for bad in (-1, "300", None, True, [1, 2], float("nan")):
            data = good(); data["nutrients"]["sodium_mg"] = bad
            self.assertIn("invalid_nutrient", self.validator.validate(data).issues, repr(bad))

    def test_nutrients_must_be_an_object(self):
        data = good(); data["nutrients"] = [1, 2, 3, 4]
        self.assertIn("invalid_nutrient", self.issues_for(data))

    # ---- reason / concern / confidence ----
    def test_reason_must_be_non_empty_text(self):
        for bad in ("", "   ", None, 5):
            data = good(); data["reason"] = bad
            self.assertIn("invalid_reason", self.issues_for(data), repr(bad))

    def test_potential_concern_must_be_a_real_boolean(self):
        for bad in ("true", 1, None):
            data = good(); data["potential_concern"] = bad
            self.assertIn("invalid_potential_concern", self.issues_for(data), repr(bad))

    def test_confidence_score_must_be_whole_number_0_to_100(self):
        for bad in (80.5, 90.0, 101, -1, "90", True, None):
            data = good(); data["confidence_score"] = bad
            self.assertIn("invalid_confidence_score", self.issues_for(data), repr(bad))

    def test_confidence_score_limits_are_inclusive(self):
        for ok in (0, 100):
            data = good(); data["confidence_score"] = ok
            self.assertTrue(self.validator.validate(data).ok, ok)

    def test_all_problems_are_reported_together(self):
        data = good(); data["reason"] = ""; data["confidence_score"] = 150; data["potential_concern"] = "yes"
        self.assertEqual(set(self.issues_for(data)), {"invalid_reason", "invalid_confidence_score", "invalid_potential_concern"})


class RecommendationValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = AIResponseValidator()

    def test_valid_recommendations(self):
        result = self.validator.validate_recommendations(fallback_reply(3))
        self.assertEqual(len(result), 3)
        self.assertEqual(set(result[0]), {"food", "reason"})

    def test_text_is_trimmed(self):
        text = json.dumps({"recommendations": [{"food": "  Oats ", "reason": " Fibre. "}]})
        self.assertEqual(self.validator.validate_recommendations(text), [{"food": "Oats", "reason": "Fibre."}])

    def test_rejects_bad_replies(self):
        bad_replies = {
            "not json": "hello",
            "wrong top-level key": json.dumps({"foods": []}),
            "extra top-level key": json.dumps({"recommendations": [{"food": "a", "reason": "b"}], "x": 1}),
            "empty list": json.dumps({"recommendations": []}),
            "too many": fallback_reply(11),
            "not a list": json.dumps({"recommendations": "milk"}),
            "item missing reason": json.dumps({"recommendations": [{"food": "Milk"}]}),
            "item with extra key": json.dumps({"recommendations": [{"food": "a", "reason": "b", "x": 1}]}),
            "blank food": json.dumps({"recommendations": [{"food": " ", "reason": "b"}]}),
            "non-string reason": json.dumps({"recommendations": [{"food": "a", "reason": 5}]}),
            "item not an object": json.dumps({"recommendations": ["Milk"]}),
            "top level list": "[]",
        }
        for name, text in bad_replies.items():
            self.assertIsNone(self.validator.validate_recommendations(text), name)


if __name__ == "__main__":
    unittest.main()
