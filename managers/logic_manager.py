from logic.confidence_policy import ConfidencePolicy
from logic.response_action import ResponseAction
from logic.rules.risk_context import RiskContext
from logic.evaluation import Evaluation
from logic.verdict import Verdict
from logic.outcomes.assessment_outcome import AssessmentOutcome
from logic.outcomes.recommendation_outcome import RecommendationOutcome


# =========== Manager ===========
class LogicManager:
    def __init__(self, rules, allergen_detector):
        self._rules = list(rules)
        self._detector = allergen_detector
        self._policy = ConfidencePolicy()

    def evaluate(self, assessment, profile, attempt_number=1):
        allergens = self._detector.detect(assessment.reason, profile.allergies) # first step, look for any allergen matches
        if allergens:
            action = ResponseAction.AVOID
        else: # empty allergens dict means no allergens matched
            action = self._policy.decide(assessment.confidence, attempt_number)

        verdict, flags = None, () # if reprompt or fallback, set as nothing

        if action in (ResponseAction.ACCEPT, ResponseAction.AVOID): # not reprompt or fallback 
            context = RiskContext(profile, assessment, allergens) # create context to pass to each rule class
            results = [rule.evaluate(context) for rule in self._rules] # evaluate the context for each rule class
            verdict = max((r.severity for r in results), default=Verdict.OK) # get the highest severity value 0,1,2. default return OK if nothing
            flags = tuple(flag for r in results for flag in r.flags) # (("sodium_mg", 650, "high"), (...), (...))

        return Evaluation(action, verdict, flags, allergens, assessment) # if action is reprompt or fallback, go to AI, else, send to GUI

    def build_outcome(self, evaluation):
        return AssessmentOutcome(evaluation)

    @staticmethod
    def build_fallback_outcome(recommendations):
        return RecommendationOutcome(recommendations)
