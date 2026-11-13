from dataclasses import dataclass

from logic.response_action import ResponseAction
from logic.verdict import Verdict


@dataclass(frozen=True)
class Evaluation: # this is the final output of logic manager. returned by LogicManager's evaluate method
    action: ResponseAction
    verdict: Verdict | None # None if response is not reliable yet
    flags: tuple
    allergens_found: dict
    assessment: object # reason and nutrition
