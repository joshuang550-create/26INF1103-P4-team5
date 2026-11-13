from ai.prompt_builder import PromptBuilder
from ai.ai_response_validator import AIResponseValidator
from exceptions.ai_response_error import AIResponseError


# =========== Manager ===========
class AIManager:
    def __init__(self, data_manager, model):
        self._data = data_manager
        self._model = model
        self._prompts = PromptBuilder()
        self._validator = AIResponseValidator()

    # =========== Public Methods ===========
    def check_food(self, profile, food_name, product=None): # product is FoodProduct from OpenFoodFactsSearcher
        return self._get_valid_assessment(profile, self._prompts.check_food_prompt(profile, food_name, product))

    def follow_up(self, profile, answers):
        return self._get_valid_assessment(profile, self._prompts.check_food_follow_up_prompt(answers))

    def reprompt(self, profile):
        return self._get_valid_assessment(profile, self._prompts.low_confidence_reprompt())

    def fallback(self, profile, retry_limit=2):
        prompt = self._prompts.fallback_prompt(profile)
        for _ in range(retry_limit):
            recommendations = self._validator.validate_recommendations(self._ask(profile, prompt))
            if recommendations is not None:
                return recommendations
            prompt = self._prompts.invalid_response_prompt(["invalid_recommendations"])
        raise AIResponseError() # failed to get valid recommendations even after reprompting

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
        raise AIResponseError() # failed to get valid response from ai after even after reprompting
