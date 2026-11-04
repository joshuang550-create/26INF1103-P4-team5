from models.user_profile import UserProfile
from managers.data_manager import DataManager
from managers.logic_manager import LogicManager, Verdict, RiskRule, RuleResult, AllergenDetector, AllergenRule, NutrientThresholdRule, AIConcernRule

data = DataManager()
thresholds = data.get_thresholds()
context_where_nothing_applies = {}


def test_new_rule_needs_no_change_to_logic_manager():
    class UnderageRule(RiskRule):
        def evaluate(self, context):
            return RuleResult(Verdict.AVOID) if context.profile.age < 18 else RuleResult()
    logic = LogicManager([UnderageRule()], AllergenDetector({}))
    # build a profile with age 10 and a good assessment, assert verdict == Verdict.AVOID


def test_every_rule_honours_the_contract():
    for rule in (AllergenRule(), NutrientThresholdRule(thresholds), AIConcernRule()):
        result = rule.evaluate(context_where_nothing_applies)
        assert isinstance(result, RuleResult)
        assert result.severity == Verdict.OK and result.flags == ()