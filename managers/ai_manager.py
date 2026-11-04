from prompts.ai_prompts import SYSTEM_INSTRUCTION, CHECK_FOOD_TEMPLATE, CHECK_FOOD_FOLLOW_UP_TEMPLATE, LOW_CONFIDENCE_REPROMPT, FALLBACK_PROMPT


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

    # =========== Read-Only Property ===========
    @property
    def system_instruction(self):
        return SYSTEM_INSTRUCTION


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

    # =========== Private Method ===========
    def _ask(self, profile, prompt):
        history = self._data.get_chat_history(profile.username) or [] # get_chat_history returns None if user has no history, so empty list instead
        response_text, new_history = self._model.send(prompt, history, self._prompts.system_instruction)
        self._data.save_chat_history(profile.username, new_history)
        return response_text

    







































def validate_ai_response(text):
    """Takes the AI's raw text.
    
        Returns:
        (dict, "No Errors") if valid.
        (None, str) if invalid, where str is the error prompt to send back to the AI.
    """
    errors = []

    # 1. Must be valid JSON (and a JSON object)   -   Edited to accept if text had already been run through json.loads() before this. To accomodate logic_manager's generic prompt response.
    if isinstance(text, (dict)):
        data = text
    else:
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError) as e:
            return None, (
                f"Your output is not valid JSON. Parsing error: {e}. "
                f"Please output a valid JSON object strictly matching the required schema."
            )

    if not isinstance(data, dict):
        return None, (
            "Your output must be a valid JSON object (dictionary), but a different data structure was received."
        )

    # 2. status
    status = data.get("status")
    if not (isinstance(status, str) and status in ("complete", "needs_follow_up")):
        errors.append("'status' must be a string with value 'complete' or 'needs_follow_up'.")

    # 3. potential_concern
    if not isinstance(data.get("potential_concern"), bool):
        errors.append("'potential_concern' must be a boolean (true or false).")

    # 4. confidence_score (whole number 0-100; rejects floats and booleans)
    score = data.get("confidence_score")
    if not (type(score) is int and 0 <= score <= 100):
        errors.append("'confidence_score' must be an integer between 0 and 100 inclusive (floats and booleans are not allowed).")

    # 5. reason
    reason = data.get("reason")
    if not (isinstance(reason, str) and reason.strip()):
        errors.append("'reason' must be a non-empty string.")

    # 6. nutrition
    nutrition = data.get("nutrition")
    if not isinstance(nutrition, dict):
        errors.append("'nutrition' must be a JSON object/dictionary.")
    else:
        if set(nutrition) != set(NUTRIENT_KEYS):
            errors.append(f"'nutrition' must contain strictly these keys: {list(NUTRIENT_KEYS)}.")
        for key in NUTRIENT_KEYS:
            val = nutrition.get(key)
            if not (is_number(val) and val >= 0):
                errors.append(f"Nutrition key '{key}' must be a non-negative number (int or float). Got: {val!r}.")

    # 7. information_needed: ONE dictionary {"question": "", "question": ""}
    needed = data.get("information_needed")
    if not isinstance(needed, dict):
        errors.append(
            "'information_needed' must be ONE JSON object where each key is a question and "
            'each value is an empty string, e.g. {"Do you drink alcohol?": "", '
            '"Do you exercise daily?": ""}. Use {} when status is \'complete\'.'
        )
    else:
        for question, answer in needed.items():
            if not question.strip():
                errors.append("'information_needed' contains an empty question key.")
            if answer != "":
                errors.append(
                    f"In 'information_needed', the value for {question!r} must be an empty "
                    f'string "" (the user fills in the answer), got {answer!r}.'
                )
        if status == "complete" and needed:
            errors.append("Inconsistency: When 'status' is 'complete', 'information_needed' must be an empty object {}.")
        if status == "needs_follow_up" and not needed:
            errors.append("Inconsistency: When 'status' is 'needs_follow_up', 'information_needed' must contain at least one question.")

    # 8. Check for missing or unexpected keys
    extra_keys = set(data) - EXPECTED_KEYS
    missing_keys = EXPECTED_KEYS - set(data)
    if extra_keys:
        errors.append(f"Unexpected extra top-level keys found: {sorted(list(extra_keys))}.")
    if missing_keys:
        errors.append(f"Missing required top-level keys: {sorted(list(missing_keys))}.")

    # If any errors were found, build the prompt f-string
    if errors:
        formatted_errors = "\n".join(f"- {e}" for e in errors)
        error_prompt = (
            f"Your previous JSON response contained the following validation errors:\n"
            f"{formatted_errors}\n\n"
            f"Please correct all the errors listed above and return only the revised, valid JSON object."
        )
        return None, error_prompt

    return data, "No Errors"

