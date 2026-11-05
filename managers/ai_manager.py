import json
import math
from dataclasses import dataclass

from prompts.ai_prompts import CHECK_FOOD_TEMPLATE, INVALID_PROMPTS, INVALID_UNKNOWN, INVALID_RESPONSE_TEMPLATE, SYSTEM_INSTRUCTION, EXPECTED_KEYS, NUTRIENT_KEYS


# =========== Helper Types ===========
@dataclass(frozen=True)
class Assessment: # this is the final output of ai manager. returned by (AIResponseValidator's validate method)? maybe, maybe not
    information_needed: list
    portion_g: float
    nutrients: dict
    reason: str
    potential_concern: bool
    confidence_score: int

    @property
    def needs_follow_up(self):
        return bool(self.information_needed)

    @property
    def confidence(self):
        return round(self.confidence_score / 10, 1)


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
        problems = [INVALID_PROMPTS.get(issue, INVALID_UNKNOWN) for issue in dict.fromkeys(issues)]
        return INVALID_RESPONSE_TEMPLATE.format(problems="\n".join(f"- {p}" for p in problems))

    # =========== Read-Only Property ===========
    @property
    def system_instruction(self):
        return SYSTEM_INSTRUCTION


class AIResponseValidator:
    def __init__(self):
        self._checks = [ # if new checks are needed, just create the private staticmethod and add it here
            self._check_keys, 
            self._check_information_needed, 
            self._check_portion, 
            self._check_nutrient, 
            self._check_reason, 
            self._check_potential_concern, 
            self._check_confidence_score
        ]

    # =========== Helper Methods ===========
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
        if set(data) != EXPECTED_KEYS:
            return ["invalid_keys"]
        return []

    @staticmethod
    def _check_information_needed(data):
        questions = data.get("information_needed")

        if isinstance(questions, list) and all(isinstance(q, str) and q.strip() for q in questions):
            return []
        
        return ["invalid_information_needed"]

    @staticmethod
    def _check_portion(data):
        portion, questions = data.get("portion_g"), data.get("information_needed")

        if not (isinstance(portion, (int, float)) and not isinstance(portion, bool) and math.isfinite(portion)) or portion < 0: 
            return ["invalid_portion"]
        
        if questions == [] and portion == 0: # assessed, but no portion given
            return ["invalid_portion"]
        
        return []

    @staticmethod
    def _check_nutrient(data):
        nutrients = data.get("nutrients")

        if not isinstance(nutrients, dict) or set(nutrients) != set(NUTRIENT_KEYS):
            return ["invalid_nutrient"]
        
        if not all((isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)) and v >= 0 for v in nutrients.values()):
            return ["invalid_nutrient"]
        
        return []

    @staticmethod
    def _check_reason(data):
        reason = data.get("reason")
        if isinstance(reason, str) and reason.strip():
            return []
        return ["invalid_reason"]

    @staticmethod
    def _check_potential_concern(data):
        potential_concern = data.get("potential_concern")
        if isinstance(potential_concern, bool):
            return []
        return ["invalid_potential_concern"]

    @staticmethod
    def _check_confidence_score(data):
        score = data.get("confidence_score")
        if type(score) is int and 0 <= score <= 100:
            return []
        return ["invalid_confidence_score"]

# =========== Manager ===========
class AIManager:
    def __init__(self, data_manager, model):
        self._data = data_manager
        self._model = model
        self._prompts = PromptBuilder()
        self._validator = AIResponseValidator()

    # =========== Public Methods ===========
    def check_food(self, profile, food_name):
        return self._get_valid_assessment(profile, self._prompts.check_food_prompt(profile, food_name))

    def follow_up(self, profile, answers):
        return self._get_valid_assessment(profile, self._prompts.check_food_follow_up_prompt(answers))

    def reprompt(self, profile):
        return self._get_valid_assessment(profile, self._prompts.low_confidence_reprompt())

    def fallback(self, profile):
        return self._ask(profile, self._prompts.fallback_prompt(profile))

    # =========== Private Method ===========
    def _ask(self, profile, prompt):
        history = self._data.get_chat_history(profile.username) or [] # get_chat_history returns None if user has no history, so empty list instead
        response = self._model.send(prompt, history, self._prompts.system_instruction)
        self._data.save_chat_history(profile.username, response.history)
        return response.text

    def _get_valid_assessment(self, profile, prompt, retry_limit=2):
        for _ in range(retry_limit):
            result = self._validator.validate(self._ask(profile, prompt)) # sends a prompt telling the ai all the issues, gets the response and runs it through validator
            if result.ok: # result.ok means issues list is empty
                return result.assessment # if validator returns no issues, return the assessment only

            prompt = self._prompts.invalid_response_prompt(result.issues) # if validator still returns issues, reprompt the ai with the new issues, up to retry_limit times
        raise ValueError("The AI did not return a valid response.") # failed to get valid response from ai after even after reprompting
