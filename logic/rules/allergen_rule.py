from logic.rules.risk_rule import RiskRule
from logic.rules.rule_result import RuleResult
from logic.verdict import Verdict


class AllergenRule(RiskRule):
    def evaluate(self, context):
        if context.allergens_found: # if allergens_found dict is True, not empty, it means an allergen was found
            return RuleResult(Verdict.AVOID)
        else:
            return RuleResult() # default Verdict.OK
