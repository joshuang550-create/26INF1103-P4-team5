import json

from prompts.ai_prompts import CHECK_FOOD_TEMPLATE, OPENFOODFACTS_TEMPLATE, CHECK_FOOD_FOLLOW_UP_TEMPLATE, LOW_CONFIDENCE_REPROMPT, FALLBACK_PROMPT, INVALID_PROMPTS, INVALID_UNKNOWN, INVALID_RESPONSE_TEMPLATE, SYSTEM_INSTRUCTION


class PromptBuilder:
    @staticmethod
    def check_food_prompt(profile, food_name, product=None): # product from OpenFoodFactsSearcher, FoodProduct object
        check_food = CHECK_FOOD_TEMPLATE.format(food_name=food_name, age=profile.age, gender=profile.gender, height=profile.height, weight=profile.weight, bmi=profile.bmi, country=profile.country, ethnicity=profile.ethnicity, medical_conditions=", ".join(profile.medical_conditions) or "none reported")
        if product:
            return check_food + "\n\n" + OPENFOODFACTS_TEMPLATE.format(barcode=product.barcode, name=product.name, brand=product.brand, quantity=product.quantity, ingredients=product.ingredients, allergens=", ".join(product.allergens) or "none listed", nutrients=json.dumps(product.nutrition_per_100g))
        return check_food

    @staticmethod
    def check_food_follow_up_prompt(answers): # answers is {"question": "answer"}
        lines = "\n".join(f"Q: {question}\nA: {answer}" for question, answer in answers.items()) # format it for the prompt
        return CHECK_FOOD_FOLLOW_UP_TEMPLATE.format(answers=lines)

    @staticmethod
    def low_confidence_reprompt():
        return LOW_CONFIDENCE_REPROMPT

    @staticmethod
    def fallback_prompt(profile):
        return FALLBACK_PROMPT.format(age=profile.age, gender=profile.gender, country=profile.country, ethnicity=profile.ethnicity, medical_conditions=", ".join(profile.medical_conditions) or "none reported")

    @staticmethod
    def invalid_response_prompt(issues): # issues is a list ["invalid_reason", "invalid_potential_concern"] from AIResponseValidator
        problems = [INVALID_PROMPTS.get(issue, INVALID_UNKNOWN) for issue in dict.fromkeys(issues)]
        return INVALID_RESPONSE_TEMPLATE.format(problems="\n".join(f"- {p}" for p in problems))

    # =========== Read-Only Property ===========
    @property
    def system_instruction(self):
        return SYSTEM_INSTRUCTION
