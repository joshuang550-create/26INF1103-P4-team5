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


# =========== Helper Classes ===========
class PromptBuilder:
    @staticmethod
    def check_food_prompt(self, profile, food_name):
        return CHECK_FOOD_TEMPLATE.format(food_name=food_name, age=profile.age, medical_conditions=", ".join(profile.medical_conditions) or "none reported")

    @staticmethod
    def check_food_follow_up_prompt(self, answers):
        pass # returns a string to be sent to an AI model

    @staticmethod
    def low_confidence_reprompt(self):
        pass # returns a string to be sent to an AI model

    @staticmethod
    def fallback_prompt(self, profile):
        pass # returns a string to be sent to an AI model

    @staticmethod
    def invalid_response_prompt(self, issues): # issues is a list ["invalid_reason", "invalid_potential_concern"] from AIResponseValidator
        return "".join(INVALID_PROMPTS[issue] for issue in issues if issue in INVALID_PROMPTS)

    # =========== Read-Only Property ===========
    @property
    def system_instruction(self):
        return SYSTEM_INSTRUCTION


class AIResponseValidator:
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

