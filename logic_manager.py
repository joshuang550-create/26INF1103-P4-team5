"""The domain brain acting on the AI's output.
"""
import json
import re
from pathlib import Path


# ===============================================================
# RESPONSE ACTION CONSTANTS
# ===============================================================
RESPONSE_ACCEPT = "accept"
RESPONSE_REPROMPT = "reprompt"
RESPONSE_FALLBACK = "fallback"
RESPONSE_AVOID = "avoid"

ALLERGENS_FILE = Path(__file__).parent / "allergens.json"
THRESHOLDS_FILE = Path(__file__).parent / "thresholds.json"

VERDICT_AVOID = "AVOID"
VERDICT_CAUTION = "CAUTION"
VERDICT_OK = "OK"

# ===============================================================
# MOCK DATA - matches ai_manager sample output as of latest update
# PARTNER_DEPENDENT: remove MOCK_* once real pipeline wiring exists
# ===============================================================

MOCK_AI_RESPONSE_ALLERGEN = {
    "status": "complete",
    "potential_concern": True,
    "confidence_score": 85,
    "reason": (
        "According to OpenFoodFacts, these prawn crackers contain "
        "crustaceans and are high in sodium"
    ),
    "information_needed": [],
}

MOCK_AI_RESPONSE = {
    "status": "complete",
    "potential_concern": True,
    "confidence_score": 90,
    "reason": (
        "According to Open Food Facts, Heinz Beanz in Tomato Sauce contains "
        "added sugar and salt, and is classifed as an ultra-processed food. "
    ),
    "information_needed":[] 
}

MOCK_USER_PROFILE = {
    "age": 45,
    "gender": "female",
    "country": "Singapore",
    "conditions": ["diabetes", "hypertension"],
}

MAX_REPROMPT_ATTEMPTS = 1

# ===============================================================
# CONFIDENCE SCORING
# ===============================================================

def calculate_response_confidence(ai_response: dict = None) -> dict:
    # Take AI' single confidence score (0-100) and rescale it t0 0.0-10.0 scale
    # Also surface the AI's own "potential_concern" flag
    if ai_response is None:
        ai_response = MOCK_AI_RESPONSE # PARTNER-DEPENDENT: remove once wired to real data

    confidence_score_raw = ai_response.get("confidence_score", 0)
    overall_score = round(confidence_score_raw/ 10, 1)

    return {
        "overall_score": overall_score,
        "potential_concern": ai_response.get("potential_concern", False),
    }


# ===============================================================
# DECISION LOGIC 
# ===============================================================

def evaluate_response_confidence(
        confidence_result: dict,
        attempt_number: int,
        min_accpetable_score: float = 5.0,
) -> str:
    """
    Decide what should happen next based on the confidence result and how many
    attempts have already been made
    - score acceptable -> ACCEPT, continue with normal flow
    - score too low, have not reprompted yet -> REPROMPT once
    - score too low, have already reprompted -> FALLBACK, give generic response:
    "We are unable to confidently determine ... We do however, recommend 
    that you eat ____ as you have ____. This will help lower your ..."
    
    Decision logic
    """
    if confidence_result["overall_score"] >= min_accpetable_score:
        return RESPONSE_ACCEPT

    elif attempt_number < MAX_REPROMPT_ATTEMPTS + 1:
        return RESPONSE_REPROMPT

    return RESPONSE_FALLBACK


# ===============================================================
# RISK SCORING
# ===============================================================

def calculate_risk_score(food_item: dict = None, user_conditions: list = None) -> float:
    """ 
    PARTNER-DEPENDENT/ BLOCKED: the real ai_manager sample does not include
    any nutrional data (n sugar/sodium fields) This function cannot run
    correctly until WE confirm where nutrition numbers come from -
    e.g. a separate food/nutrition database lookup, or an added field in
    the AI response. Raising explicitly instead of faking a number, since a
    wrong risk score in a health context is worse than no risk score.
    """

    raise NotImplementedError(
        "calculate_risk_score() is blocked: no nutrional data present in "
        "the real ai_manager response sample. Confrim data source with team"
    )

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


# ===============================================================
# GENERIC FALLBACK RESPONSE
# NOTE: CONCEPTUALLY belongs in ai_manager (build promts / fetch
# content rather than deciding) idk if we should move it or keep it here
# ===============================================================

def generate_generic_response_prompt(user_profile: dict = None) -> str:
    """should the response confidence be poor even after reprompt, build a
    prompt that ignores the original request food item and ask for food
    recos based on user profile and conditions
    """
    if user_profile is None:
        user_profile = MOCK_USER_PROFILE # PARTNER-DEPENDENT: remove once wired to real data

    age = user_profile.get("age")
    gender = user_profile.get("gender")
    country = user_profile.get("country")
    conditions = ", ".join(user_profile.get("conditions", []))

    return (
        f"I am a {age}-year-old {gender} from {country} with the following medical conditions: {conditions}. "
        f"What are the best foods I should eat given my medical conditions?"
    )
    

def generate_generic_response(user_profile: dict = None) -> dict:
    """
    Use a ranked database to find the best foods to eat based on medical
    conditions. NOT IMPLEMENTED - requires a food/conditions database that 
    doesn't exist yet (idk whr it exists), and agreed conflict-resolution strategy
    """
    raise NotImplementedError(
        "generate_generic_response() requires a ranked food/conditions database "
        "database that has not built yet, and a decided conflict -"
        "resolution strategy"
    )

def load_allergens(path=ALLERGENS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["allergen_synonyms"]

def detect_allergens(text, allergen_synonyms=None):
    """Return {category: [matched word]} for every allergen word detected"""
    if allergen_synonyms is None:
        allergen_synonyms = load_allergens()

    found = {}
    for category, words in allergen_synonyms.items():
        for word in words:
            if re.search(rf"\b{re.escape(word)}s?\b", text, re.IGNORECASE):
                found.setdefault(category, []).append(word)
    return found

def build_allergen_warning(found):
    parts = []
    for category, words in found.items():
        group = category.split("_")[0].title()
        if group not in parts:
            parts.append(group)
        for word in words:
            parts.append(word.title())
    return (
        f"  Allergens Found: {', '.join(parts)}\n"
        f"  Warning        : Avoid this food, allergen detected"
    )
        
    

# ===================================================
# TEMPORARY MOCK FUNCTIONS FOR TESTING PURPOSES
# ===================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Normal Food (Heinz Beanz)")
    print("=" * 50)
    confidence_result = calculate_response_confidence()
    action = evaluate_response_confidence(confidence_result, attempt_number=1)
    print(f"    Confidence score : {confidence_result['overall_score']} / 10")
    print(f"    Potential concern: {confidence_result['potential_concern']}")
    print(f"    Action           : {action.upper()}")

    '''Mock Response Allergen Detection'''
    print("=" * 50)
    print("TEST 2: Allergen Food (Prawn Crackers)")
    print("=" * 50)
    found = detect_allergens(MOCK_AI_RESPONSE_ALLERGEN["reason"])
    if found:
        print(build_allergen_warning(found))
    else:
        print("No Allergens detected")

    '''Risk Score skipped temporarily, to test allergen detection'''
    print()
    print("=" * 50)
    print("TEST 1: (Heinz Beanz)")
    print("=" * 50)
    try:
        risk = calculate_risk_score()
        print("Risk Score:", risk)
    except NotImplementedError as e:
        print("Risk score skipped:", e)


    if action == RESPONSE_FALLBACK:
        prompt = generate_generic_response_prompt()
        print("Generic fallback prompt:", prompt)