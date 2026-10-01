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
    

    
    
    pass





# Definitely should add more work for the logic_manager to do, currently all it does is check confidence and risk scores, which are simple < > comparisons.
# POSSIBLE IDEAS  --  neither are good cause not really logic_manager, more ai_manager and io_manager
def generate_generic_response_prompt():
    # should the response confidence be poor even after reprompt, call this function to generate a response ignoring the food they wanted to check, and just recommend food to eat based on the user profile's medical conditions.
    # This function will generate a prompt roughly saying the user's profile info, medical conditions, then ask "What are the best foods i should eat given my medical conditions."
    pass


def generate_generic_response():
    # use a database to find the best foods to eat based on medical conditions. Ranked database. Issue is conflictions, what if best for this is bad for that and you have both this and that?
    pass

