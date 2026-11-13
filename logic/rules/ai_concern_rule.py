from logic.rules.risk_rule import RiskRule
from logic.rules.rule_result import RuleResult
from logic.verdict import Verdict


class AIConcernRule(RiskRule):
    def evaluate(self, context):
        if context.assessment.potential_concern: # if there is even 1 potential concern, verdict is CAUTION
            return RuleResult(Verdict.CAUTION)
        return RuleResult() # not applicable, default OK
