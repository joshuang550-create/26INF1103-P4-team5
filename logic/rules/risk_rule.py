from abc import ABC, abstractmethod


class RiskRule(ABC):
    @abstractmethod
    def evaluate(self, context):
        pass # returns RuleResult(). If rule doesnt apply, returns deafault (OK, no flags)
