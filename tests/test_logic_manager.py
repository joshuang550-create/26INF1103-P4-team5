"""Business rules, severity scoring, confidence routing and outcome objects."""
import unittest

from managers.ai_manager import Assessment
from managers.logic_manager import (AllergenDetector, AllergenRule, AIConcernRule, AssessmentOutcome, ConfidencePolicy,
                                    LogicManager, NutrientThresholdRule, RecommendationOutcome, ResponseAction,
                                    RiskContext, RiskRule, RuleResult, Verdict)
from tests.helpers import NUTRIENT_KEYS, make_profile

THRESHOLDS = {
    "sodium_mg": {"moderate": 300, "high": 600, "relevant_conditions": ["hypertension", "blood pressure"]},
    "sugar_g": {"moderate": 10, "high": 22.5, "relevant_conditions": ["diabet"]},
}
SYNONYMS = {"shellfish_crustacean": ["shrimp", "crab"], "nuts": ["peanut"]}


def assessment(confidence=90, concern=False, reason="Fine.", **nutrients):
    values = {key: 0 for key in NUTRIENT_KEYS}
    values.update(nutrients)
    return Assessment(information_needed=[], portion_g=100, nutrients=values, reason=reason,
                      potential_concern=concern, confidence_score=confidence)


def context(profile, ai_assessment, allergens=None):
    return RiskContext(profile, ai_assessment, allergens or {})


class AllergenRuleTests(unittest.TestCase):
    def test_allergen_found_means_avoid(self):
        result = AllergenRule().evaluate(context(make_profile(), assessment(), {"nuts": ["peanut"]}))
        self.assertEqual(result.severity, Verdict.AVOID)

    def test_no_allergen_means_ok(self):
        self.assertEqual(AllergenRule().evaluate(context(make_profile(), assessment())).severity, Verdict.OK)


class NutrientThresholdRuleTests(unittest.TestCase):
    def setUp(self):
        self.rule = NutrientThresholdRule(THRESHOLDS)
        self.hypertensive = make_profile(["hypertension"])

    def run_rule(self, profile, **nutrients):
        return self.rule.evaluate(context(profile, assessment(**nutrients)))

    def test_below_moderate_is_ok(self):
        result = self.run_rule(self.hypertensive, sodium_mg=299.9)
        self.assertEqual((result.severity, result.flags), (Verdict.OK, ()))

    def test_moderate_boundary_is_inclusive_and_gives_caution(self):
        result = self.run_rule(self.hypertensive, sodium_mg=300)
        self.assertEqual(result.severity, Verdict.CAUTION)
        self.assertEqual(result.flags, (("sodium_mg", 300, "moderate"),))

    def test_value_equal_to_high_limit_is_still_moderate(self):
        self.assertEqual(self.run_rule(self.hypertensive, sodium_mg=600).severity, Verdict.CAUTION)

    def test_above_high_gives_avoid_with_flag(self):
        result = self.run_rule(self.hypertensive, sodium_mg=600.1)
        self.assertEqual(result.severity, Verdict.AVOID)
        self.assertEqual(result.flags, (("sodium_mg", 600.1, "high"),))

    def test_nutrient_ignored_when_user_has_no_relevant_condition(self):
        self.assertEqual(self.run_rule(make_profile(["asthma"]), sodium_mg=5000).severity, Verdict.OK)

    def test_condition_matching_is_by_keyword(self):  # "diabet" matches "type 2 diabetes"
        self.assertEqual(self.run_rule(make_profile(["Type 2 Diabetes"]), sugar_g=30).severity, Verdict.AVOID)

    def test_one_high_outweighs_moderate_flags(self):
        profile = make_profile(["hypertension", "diabetes"])
        result = self.run_rule(profile, sodium_mg=400, sugar_g=30)
        self.assertEqual(result.severity, Verdict.AVOID)
        self.assertEqual(len(result.flags), 2)

    def test_nutrient_missing_from_assessment_is_skipped(self):
        bare = Assessment([], 100, {}, "Fine.", False, 90)
        self.assertEqual(self.rule.evaluate(context(self.hypertensive, bare)).severity, Verdict.OK)


class AIConcernRuleTests(unittest.TestCase):
    def test_concern_gives_caution_never_avoid(self):
        self.assertEqual(AIConcernRule().evaluate(context(make_profile(), assessment(concern=True))).severity, Verdict.CAUTION)

    def test_no_concern_is_ok(self):
        self.assertEqual(AIConcernRule().evaluate(context(make_profile(), assessment())).severity, Verdict.OK)


class AllergenDetectorTests(unittest.TestCase):
    def setUp(self):
        self.detector = AllergenDetector(SYNONYMS)

    def test_flags_only_allergens_the_user_has(self):
        found = self.detector.detect("Contains shrimp paste and peanut oil.", ["shrimp allergy"])
        self.assertEqual(found, {"shellfish_crustacean": ["shrimp"]})

    def test_other_users_allergen_is_not_flagged(self):
        self.assertEqual(self.detector.detect("Contains shrimp.", ["peanut allergy"]), {})

    def test_case_insensitive_and_plural(self):
        self.assertIn("shellfish_crustacean", self.detector.detect("Fresh CRABS on toast", ["crab allergy"]))

    def test_word_boundaries_avoid_false_positives(self):
        self.assertEqual(self.detector.detect("A shrimpy-tasting broth", ["shrimp allergy"]), {})

    def test_no_allergies_means_nothing_flagged(self):
        self.assertEqual(self.detector.detect("shrimp shrimp shrimp", []), {})

    def test_multiple_allergies(self):
        found = self.detector.detect("shrimp and peanut", ["shrimp allergy", "peanut allergy"])
        self.assertEqual(set(found), {"shellfish_crustacean", "nuts"})


class ConfidencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = ConfidencePolicy()  # min 5.0, one reprompt

    def test_good_score_is_accepted(self):
        self.assertEqual(self.policy.decide(5.0, 1), ResponseAction.ACCEPT)
        self.assertEqual(self.policy.decide(9.0, 1), ResponseAction.ACCEPT)

    def test_low_first_attempt_is_reprompted(self):
        self.assertEqual(self.policy.decide(4.9, 1), ResponseAction.REPROMPT)

    def test_low_after_reprompt_falls_back(self):
        self.assertEqual(self.policy.decide(4.9, 2), ResponseAction.FALLBACK)

    def test_custom_limits(self):
        policy = ConfidencePolicy(min_score=8.0, max_reprompts=2)
        self.assertEqual(policy.decide(7.9, 2), ResponseAction.REPROMPT)
        self.assertEqual(policy.decide(7.9, 3), ResponseAction.FALLBACK)


class LogicManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = LogicManager([AllergenRule(), NutrientThresholdRule(THRESHOLDS), AIConcernRule()], AllergenDetector(SYNONYMS))

    def test_clean_food_is_ok(self):
        evaluation = self.manager.evaluate(assessment(), make_profile())
        self.assertEqual((evaluation.action, evaluation.verdict, evaluation.flags), (ResponseAction.ACCEPT, Verdict.OK, ()))

    def test_highest_severity_wins(self):
        evaluation = self.manager.evaluate(assessment(concern=True, sodium_mg=900), make_profile(["hypertension"]))
        self.assertEqual(evaluation.verdict, Verdict.AVOID)

    def test_allergen_forces_avoid_even_with_low_confidence(self):
        evaluation = self.manager.evaluate(assessment(confidence=5, reason="Made with shrimp."), make_profile(["shrimp allergy"]))
        self.assertEqual((evaluation.action, evaluation.verdict), (ResponseAction.AVOID, Verdict.AVOID))
        self.assertIn("shellfish_crustacean", evaluation.allergens_found)

    def test_low_confidence_gives_no_verdict_yet(self):
        evaluation = self.manager.evaluate(assessment(confidence=20), make_profile(), attempt_number=1)
        self.assertEqual((evaluation.action, evaluation.verdict, evaluation.flags), (ResponseAction.REPROMPT, None, ()))

    def test_low_confidence_after_reprompt_is_fallback(self):
        self.assertEqual(self.manager.evaluate(assessment(confidence=20), make_profile(), attempt_number=2).action, ResponseAction.FALLBACK)

    def test_new_rules_can_be_plugged_in(self):  # open/closed principle
        class AlwaysCaution(RiskRule):
            def evaluate(self, ctx):
                return RuleResult(Verdict.CAUTION)
        manager = LogicManager([AlwaysCaution()], AllergenDetector({}))
        self.assertEqual(manager.evaluate(assessment(), make_profile()).verdict, Verdict.CAUTION)

    def test_no_rules_defaults_to_ok(self):
        self.assertEqual(LogicManager([], AllergenDetector({})).evaluate(assessment(), make_profile()).verdict, Verdict.OK)


class OutcomeTests(unittest.TestCase):
    def test_assessment_outcome_to_dict(self):
        manager = LogicManager([NutrientThresholdRule(THRESHOLDS)], AllergenDetector(SYNONYMS))
        evaluation = manager.evaluate(assessment(sodium_mg=700), make_profile(["hypertension"]))
        data = manager.build_outcome(evaluation).to_dict()
        self.assertEqual((data["headline"], data["severity"]), ("AVOID", "AVOID"))
        self.assertEqual(data["details"]["flags"], [{"nutrient": "sodium_mg", "value": 700, "level": "high"}])
        self.assertEqual(data["details"]["confidence"], 9.0)
        self.assertEqual(data["details"]["allergens_found"], {})

    def test_fallback_outcome_is_undetermined(self):
        outcome = LogicManager.build_fallback_outcome([{"food": "Milk", "reason": "Calcium."}])
        data = outcome.to_dict()
        self.assertIsInstance(outcome, RecommendationOutcome)
        self.assertEqual((data["headline"], data["severity"]), ("UNDETERMINED", None))
        self.assertEqual(data["details"]["recommendations"], [{"food": "Milk", "reason": "Calcium."}])

    def test_outcome_is_not_changed_by_editing_the_source_list(self):
        source = [{"food": "Milk", "reason": "Calcium."}]
        outcome = RecommendationOutcome(source)
        source[0]["food"] = "Changed"
        self.assertEqual(outcome.details()["recommendations"][0]["food"], "Milk")

    def test_verdict_ordering(self):
        self.assertLess(Verdict.OK, Verdict.CAUTION)
        self.assertLess(Verdict.CAUTION, Verdict.AVOID)


if __name__ == "__main__":
    unittest.main()
