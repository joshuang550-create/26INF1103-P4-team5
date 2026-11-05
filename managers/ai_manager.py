import json
from dataclasses import dataclass

from prompts.ai_prompts import SYSTEM_INSTRUCTION, CHECK_FOOD_TEMPLATE, CHECK_FOOD_FOLLOW_UP_TEMPLATE, LOW_CONFIDENCE_REPROMPT, FALLBACK_PROMPT, INVALID_PROMPTS


# =========== Helper Types ===========
@dataclass(frozen=True)
class Assessment: # this is the final output of ai manager. returned by (AIResponseValidator's validate method)? maybe, maybe not
    reason: str
    potential_concern: bool
    confidence_score: int
    nutrition: dict
    status: str
    information_needed: dict


@dataclass(frozen=True)
class ValidationResult: # this is the final output of AIResponseValidator. Allows both assessment and issues to be returned as one rather than either or, leading to isinstance check in main
    assessment: Assessment | None = None
    issues: tuple = ()

    @property
    def ok(self):
        return not self.issues


# =========== Helper Classes ===========
class PromptBuilder:
    @staticmethod
    def check_food_prompt(profile, food_name):
        return CHECK_FOOD_TEMPLATE.format(food_name=food_name, age=profile.age, medical_conditions=", ".join(profile.medical_conditions) or "none reported")

    @staticmethod
    def check_food_follow_up_prompt(answers):
        pass # returns a string to be sent to an AI model

    @staticmethod
    def low_confidence_reprompt():
        pass # returns a string to be sent to an AI model

    @staticmethod
    def fallback_prompt(profile):
        pass # returns a string to be sent to an AI model

    @staticmethod
    def invalid_response_prompt(issues): # issues is a list ["invalid_reason", "invalid_potential_concern"] from AIResponseValidator
        return "".join(INVALID_PROMPTS[issue] for issue in issues if issue in INVALID_PROMPTS)

    # =========== Read-Only Property ===========
    @property
    def system_instruction(self):
        return SYSTEM_INSTRUCTION


class AIResponseValidator:
    def __init__(self):
        self.checks = [ # if new checks are needed, just create the private staticmethod and add it here
            self._check_keys,
            self._check_nutrient,
            self._check_status,
            self._check_potential_concern,
            self._check_confidence_score,
            self._check_reason,
            self._check_information_needed
        ]

    # =========== Helper Method ===========
    @staticmethod
    def _parse(response_text):
        try:
            data = json.loads(response_text) if isinstance(response_text, str) else response_text # if string, json.loads to a dict, else keep it as is
        except json.JSONDecodeError:
            return None, "invalid_json"

        if not isinstance(data, dict):
            return None, "invalid_structure" # if not a dict

        return data, None # valid data


    # =========== Public Method ===========
    def validate(self, response_text):
        data, issue = self._parse(response_text)

        if issue:
            return ValidationResult(issues=(issue,)) # if response_text cannot be parsed properly, not a dict
        
        issues = [i for check in self._checks for i in check(data)] # response_text is a dict, then run every check in self.checks 

        if issues:
            return ValidationResult(issues=tuple(issues)) # if there is even 1 issue, return issues without assessment

        return ValidationResult(assessment=Assessment(**data)) # if there is no issues at all, return assessment without issues

    # =========== Private Methods ===========
    @staticmethod
    def _check_keys(data):
        pass

    @staticmethod
    def _check_nutrient(data):
        pass

    @staticmethod
    def _check_status(data):
        pass

    @staticmethod
    def _check_potential_concern(data):
        pass

    @staticmethod
    def _check_confidence_score(data):
        pass

    @staticmethod
    def _check_reason(data):
        pass

    @staticmethod
    def _check_information_needed(data):
        pass

    # takes in response_text from AIManager's _ask()

    # returns assessment object for LogicManager

    # 1. check isinstance json/dict (response_text might be string so need to convert to dict fist, check later)

    # 2. check response_text against EXPECTED_KEYS   -   if missing or extra keys, append to issues list  -   run through all tests first and get all the errors

    # 3. check response_text["nutrient"] against NUTRIENT_KEYS   -   if response_text's nutrients != NUTRIENT_KEYS or values are not positive int/float, append to issues list

    # 4. check value of response_text["status"]   -   isinstance str and  in ("complete", "needs_follow_up")

    # 5. check value of response_text["potential_concern"]   -   isinstance bool

    # 6. check value of response_text["confidence_score"]   -   isinstance int and between 0 and 100 inclusive

    # 7. check value of response_text["reason"]   -   isinstance str and not empty after strip()

    # 8. check value of response_text["information_needed"]   -   isinstance dict, keys must not be empty, values must be empty, if status=="complete" {}, if status=="needs_follow_up" {"...":"", "...":""}

    # 9. if there is even 1 issue, return issues   -   issues is a list ["invalid_nutrient", "invalid_reason"]

    # 9. if not issues, then create and return assessment   -   assessment is an object instance of Assessment


# =========== Manager ===========
class AIManager:
    def __init__(self, data_manager, model):
        self._data = data_manager
        self._model = model
        self._prompts = PromptBuilder()

    # =========== Public Methods ===========
    def check_food(self, profile, food_name):
        return self._ask(profile, self._prompts.check_food_prompt(profile, food_name))

    def follow_up(self, profile, answers):
        return self._ask(profile, self._prompts.check_food_follow_up_prompt(answers))

    def reprompt(self, profile):
        return self._ask(profile, self._prompts.low_confidence_reprompt())

    def fallback(self, profile):
        return self._ask(profile, self._prompts.fallback_prompt(profile))

    def invalid(self, profile, issues):
        return self._ask(profile, self._prompts.invalid_response_prompt(issues))

    # =========== Private Method ===========
    def _ask(self, profile, prompt):
        history = self._data.get_chat_history(profile.username) or [] # get_chat_history returns None if user has no history, so empty list instead
        response_text, new_history = self._model.send(prompt, history, self._prompts.system_instruction)
        self._data.save_chat_history(profile.username, new_history)
        return response_text

