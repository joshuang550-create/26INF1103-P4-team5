import re
from abc import ABC, abstractmethod
from enum import IntEnum, Enum
from dataclasses import dataclass


# =========== Helper Types ===========
class Verdict(IntEnum):
    OK = 0
    CAUTION = 1
    AVOID = 2


class ResponseAction(Enum):
    ACCEPT = "accept"
    REPROMPT = "reprompt"
    FALLBACK = "fallback"
    AVOID = "avoid"


@dataclass(frozen=True)
class RuleResult:
    severity: Verdict = Verdict.OK
    flags: tuple = () # ("sodium_mg", 650, "high")


@dataclass(frozen=True)
class RiskContext: # this helps RiskRule later so that it only takes the context it needs (allergens_found is only needed for AllergenRule)
    profile: object
    assessment: object
    allergens_found: dict


@dataclass(frozen=True)
class Evaluation: # this is the final output of logic manager. returned by LogicManager's evaluate method
    action: ResponseAction
    verdict: Verdict | None # None if response is not reliable yet
    flags: tuple
    allergens_found: dict
    assessment: object # reason and nutrition


# =========== Interface ===========
class RiskRule(ABC):
    @abstractmethod
    def evaluate(self, context):
        pass # returns RuleResult(). If rule doesnt apply, returns deafault (OK, no flags)


# =========== Rules ===========
class AllergenRule(RiskRule):
    def evaluate(self, context):
        if context.allergens_found: # if allergens_found dict is True, not empty, it means an allergen was found
            return RuleResult(Verdict.AVOID)
        else:
            return RuleResult() # default Verdict.OK


class NutrientThresholdRule(RiskRule):
    def __init__(self, thresholds):
        self._thresholds = thresholds

    def evaluate(self, context):
        flags = []

        for nutrient, limits in self._thresholds.items():
            if not context.profile.has_condition_matching(limits["relevant_conditions"]): # if the words in relevant_conditions matches any words in MedicalCondition's _conditions
                continue

            value = context.assessment.nutrition.get(nutrient) # try to get the value of the nutrient in assessment, if that nutrient is not in assessment, None, else get the value (in mg/g)
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
    

class AIConcernRule(RiskRule):
    def evaluate(self, context):
        if context.assessment.potential_concern: # if there is even 1 potential concern, verdict is CAUTION
            return RuleResult(Verdict.CAUTION)
        return RuleResult() # not applicable, default OK


# =========== Single-Purpose Helpers ===========
class AllergenDetector:
    def __init__(self, synonyms):
        self._synonyms = synonyms # from DataManager.get_allergens()

    def detect(self, text):
        found = {}
        for category, words in self._synonyms.items(): # {category: [word, word, word], category: [word, word, word]}
            for word in words:
                if re.search(rf"\b{re.escape(word)}s?\b", text, re.IGNORECASE):
                    found.setdefault(category, []).append(word) # if category exists in found, add to it, else create it
        return found


class ConfidencePolicy:
    min_score = 5.0
    max_reprompts = 1

    def decide(self, score, attempt_number):
        if score >= self.min_score:
            return ResponseAction.ACCEPT # good enough

        if attempt_number < self.max_reprompts + 1:
            return ResponseAction.REPROMPT # not good enough, reprompt AI to try for better score

        return ResponseAction.FALLBACK # not good enough even after reprompt, use fallback response


# =========== Manager ===========
class LogicManager:
    def __init__(self, rules, allergen_detector):
        self._rules = list(rules)
        self._detector = allergen_detector # aggregation for DataManager to pass the synonyms to AllergenDetector
        self._policy = ConfidencePolicy()

    def evaluate(self, assessment, profile, attempt_number=1):
        allergens = self._detector.detect(assessment.reason) # first step, look for any allergen matches
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





# assessment here is dict not object, replace above code assessment methods with dict key to test

# from managers.data_manager import DataManager
# from models.user_profile import UserProfile
 
# data = DataManager()

# rules = [AllergenRule(), NutrientThresholdRule(data.get_thresholds()), AIConcernRule()]
# allergen_detector = AllergenDetector(data.get_allergens())

# reason = "The chocolate protein bar contains caffeine, which can potentially shrimp raise blood pressure, a concern given your medical history of high blood pressure. Additionally, maltitol is a sugar alcohol that can sometimes cause gastrointestinal distress, and the peanuts are a hard texture that might aggravate TMJ symptoms."
# assessment = {"reason": reason, "potential_concern": True, "confidence_score": 8.84, "nutrition": {"sodium_mg": 650, "calcium_g": 10, "sugar_g": 10}, "status": "complete", "information_needed": None}
# profile = UserProfile.create(username="Jeff", plain_password="jeff", age=23, height=169.95, weight=73.55, country="Singapore", ethnicity="Chinese", gender="Male", medical_conditions=["shrimp allergy", "Diabet", "High Cholesterol", "Hypertension"])

# lm = LogicManager(rules, allergen_detector)
# evaluation = lm.evaluate(assessment, profile, attempt_number=1)

# print()
# print(evaluation.action)
# print()
# print(evaluation.verdict)
# print()
# print(evaluation.flags)
# print()
# print(evaluation.allergens_found)
# print()
# print(evaluation.assessment)
# print()