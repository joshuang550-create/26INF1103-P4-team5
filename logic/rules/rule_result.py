from dataclasses import dataclass

from logic.verdict import Verdict


@dataclass(frozen=True)
class RuleResult:
    severity: Verdict = Verdict.OK
    flags: tuple = () # ("sodium_mg", 650, "high")
