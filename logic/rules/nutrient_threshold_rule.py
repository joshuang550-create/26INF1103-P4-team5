from logic.rules.risk_rule import RiskRule
from logic.rules.rule_result import RuleResult
from logic.verdict import Verdict


class NutrientThresholdRule(RiskRule):
    def __init__(self, thresholds):
        self._thresholds = thresholds

    def evaluate(self, context):
        flags = []

        for nutrient, limits in self._thresholds.items():
            if not context.profile.has_condition_matching(limits["relevant_conditions"]): # if the words in relevant_conditions matches any words in MedicalCondition's _conditions
                continue

            value = context.assessment.nutrients.get(nutrient) # try to get the value of the nutrient in assessment, if that nutrient is not in assessment, None, else get the value (in mg/g)
            if value is None:
                continue
            if value > limits["high"]:
                flags.append((nutrient, value, "high")) # create a flag that shows the nutrient like sodium, and the value in the food user is checking, and high/moderate
            elif value >= limits["moderate"]:
                flags.append((nutrient, value, "moderate"))

        if any(level == "high" for _, _, level in flags):
            return RuleResult(Verdict.AVOID, tuple(flags)) # if there is even 1 high, return AVOID with the flags
        if flags:
            return RuleResult(Verdict.CAUTION, tuple(flags)) # if there is no high and at least 1 moderate, return CAUTION with the flags

        return RuleResult() # default OK, no flags
