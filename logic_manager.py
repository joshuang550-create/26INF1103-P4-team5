"""The domain brain acting on the AI's output.
"""
from enum import Enum

MOCK_AI_RESPONSE = {
    "food_item": "Peanut Butter",
    "confidence score": {
        "source_reliability": 0.82,
        "nutritional match": 0.65,
        "condition_relevance": 0.40,
    },
    "nutrional_info": {
        "sugar_g": 3.0,
        "sodium_mg": 150.0,
        "carbs_g": 8.0,
    },
}

MOCK_USER_PROFILE = {
    "age": 30,
    "gender": "female",
    "country": "Singapore",
    "medical_conditions": ["diabetes", "hypertension"],
}

class ResponseAction(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    FALLBACK = "fallback"

MAX_REPROMPT_ATTEMPTS = 1

def calculate_response_confidence(ai_response: dict = None, low_field_threshold: float = 0.5) -> dict:
    # Confidence score should be something like how confident we (the developers) are that this response from the ai is reliable and can be trusted.
    # From the JSON response, take the key-value pairs that store all the confidence scores and do some math to calculate an overall respose confidence score from 0.0 to 10.0
    # we can also add on to this to specifically tell the user if any specific confidence score is lower than 50%. Tell the user that this specific piece of info may not be reliable.
    # This confidence score will affect logic flow. If the score is very low and unsatisfactory, we will reprompt the AI one more time (only one more time) to try and get better more reliable sources for their information, then rerun this sequence to check if it is satisfactory, if it is continue as per normal, if not, give a generic output saying "We are unable to confidently determine ... We do however, recommend that you eat xxx as you have xxx. This will help lower your ..."
    if ai_response is None:
        ai_response = MOCK_AI_RESPONSE # CHANGE ACCORDINGLY, WAIT FOR AI

    confidence_fields = ai_response.get("confidence score", {})

    if not confidence_fields:
        return {"overall_score": 0.0, "low_confidence_fields": []}

    score = list(confidence_fields. values())
    overall_score = round((sum(score) / len(score)) * 10, 1) # CHANGE ARRCODINGLY, WAIT FOR AI

    low_confidence_fields = [
        field for field, score in confidence_fields.items()
        if score < low_field_threshold
    ]

    return {
        "overall_score": overall_score,
        "low_confidence_fields": low_confidence_fields
    }


def calculate_risk_score(food_item: dict = None, user_conditions: list = None) -> float:
    # I think the risk score is something like from a scale of 0.0 to 10.0, how risky is it for you to eat this food item based on your conditions.
    # This risk score does not affect logic at all, it is purely a number we show the user to tell them whether they should eat the food or not.
    
    """ CHANGE ACCORDINGLY, WAIT FOR AI 
    get_codition_risk() placeholder ; real version needs a lookup table or data base keyed by condition + nutrient thresholds """

    if food_item is None:
        food_item = MOCK_AI_RESPONSE # CHANGE ACCORDINGLY, WAIT FOR AI
    if user_conditions is None:
        user_conditions = MOCK_USER_PROFILE.get("conditions", []) # CHANGE ACCORDINGLY, WAIT FOR AI

    if not user_conditions:
        return 0.0

    risk_points = sum(get_condition_risk(condition, food_item) for condition in user_conditions)
    max_possible_points = len(user_conditions) * 10  # Assuming each condition can contribute a maximum of 10 points to the risk score
    return round((risk_points / max_possible_points) * 10, 1)  # Scale to 0.0 - 10.0


# Definitely should add more work for the logic_manager to do, currently all it does is check confidence and risk scores, which are simple < > comparisons.
# POSSIBLE IDEAS  --  neither are good cause not really logic_manager, more ai_manager and io_manager

def get_condition_risk(food_item: dict, condition: str) -> int:
    """
    RETURN RISK CONTRIBUTIION (0-10) FOR A SINGLE CONDITION AGAINST FOOD
    
    CHANGE ACCORDINGLY, WAIT FOR AI
    THROWAWAY PLACEHOLDER SO calculate_risk_score() CAN BE TESTED
    """
    nutritional_info = food_item.get("nutrional_info", {})

    if condition == "diabetes":
        return min(10, int(nutritional_info.get("sugar_g", 0)))  # Example: sugar content contributes to risk
    if condition == "hypertension":
        return min(10, int(nutritional_info.get("sodium_mg", 0) / 100))  # Example: sodium content contributes to risk
    
    return 0 # unknown condition - no risk data available


#===================================================
# NOTE: the two function below should belong to ai_manager - they generate prompts
# and fetch/produce content rather than making decisions.
def generate_generic_response_prompt(user_profile: dict = None) -> str:
    # should the response confidence be poor even after reprompt, call this function to generate a response ignoring the food they wanted to check, and just recommend food to eat based on the user profile's medical conditions.
    # This function will generate a prompt roughly saying the user's profile info, medical conditions, then ask "What are the best foods i should eat given my medical conditions."
    
    if user_profile is None:
        user_profile = MOCK_USER_PROFILE # CHANGE ACCORDINGLY, WAIT FOR AI

    age = user_profile.get("age")
    gender = user_profile.get("gender")
    country = user_profile.get("country")
    conditions = ", ".join(user_profile.get("conditions", []))

    prompt = (
        f"I am a {age}-year-old {gender} from {country} with the following medical conditions: {conditions}. "
        f"What are the best foods I should eat given my medical conditions?"
    )
    return prompt

def generate_generic_response():
    # use a database to find the best foods to eat based on medical conditions. Ranked database. Issue is conflictions, what if best for this is bad for that and you have both this and that?
    pass

