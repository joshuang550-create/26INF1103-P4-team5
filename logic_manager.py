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
    "nutrition":{ # example one serving
        "sodium_mg": 520,
        "sugar_g": 0.5,
        "saturated_fat_g": 3.4,
        "trans_fat_g": 0.0,
    },
    "reason": (
        "According to OpenFoodFacts, these prawn crackers contain "
        "crustaceans and are high in sodium"
    ),
    "information_needed": {}, # a dict now: {question : ""}. Empty when complete
}

MOCK_AI_RESPONSE = {
    "status": "complete",
    "potential_concern": True,
    "confidence_score": 90,
    "nutrition":{ # example one serving
            "sodium_mg": 480,
            "sugar_g": 0.5,
            "saturated_fat_g": 3.4,
            "trans_fat_g": 0.0,
    },
    "reason": (
        "According to Open Food Facts, Heinz Beanz in Tomato Sauce contains "
        "added sugar and salt, and is classifed as an ultra-processed food. "
    ),
    "information_needed":{} 
}

MOCK_USER_PROFILE = { # same kets as profiles in json
    "age": 45,
    "gender": "female",
    "ethnicity": "chinese",
    "country": "Singapore",
    "medical_conditions": ["diabetes", "high blood pressure"],
}

MAX_REPROMPT_ATTEMPTS = 1

# ===============================================================
# CONFIDENCE SCORING
# ===============================================================

def calculate_response_confidence(ai_response: dict) -> dict:
    # Take AI' single confidence score (0-100) and rescale it t0 0.0-10.0 scale
    # Also surface the AI's own "potential_concern" flag
    # If AI response is missing (None), we have no answer, score 0 and potential concern is none
    if ai_response is None:
        return {"overall_score": 0.0, "potential_concern": None}

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

def load_thresholds(path=THRESHOLDS_FILE):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)["nutrients"]

def user_has_condition(user_conditions: list, keywords: list) -> bool:
    """True if any keyword appears inside any of the user's conditions.
    Users type conditions freely (io_manager stores e.g. "high blood pressure"),
    so we match keywords inside the test : "blood pressure" is in
    "high blood pressure"
    """
    for condition in user_conditions:
        for keyword in keywords:
            if keyword.lower() in condition.lower():
                return True
    return False

def check_nutrition(nutrition: dict, user_conditions: list, thresholds: dict | None = None) -> list:
    """Compare the AI's nurtition numbers with thresholds.json.
   
   Only nutrients that matter for the user's conditions are checked.
   Return list of flags
   Empty list means nothing crossed thresholds
   """
    if thresholds is None:
        thresholds = load_thresholds()
 
    flags = []
    for nutrient, limits in thresholds.items():
        if not user_has_condition(user_conditions, limits["relevant_conditions"]):
            continue  # this nutrient does not matter for this user
 
        value = nutrition.get(nutrient)
        if value is None:
            continue
 
        if value > limits["high"]:
            level = "high"
        elif value >= limits["moderate"]:
            level = "moderate"
        else:
            continue  # under the limit, nothing to flag
 
        flags.append({"nutrient": nutrient, "value": value, "level": level})
    return flags

def determine_verdict(flags, allergens_found, potential_concern):
    if allergens_found:
        return VERDICT_AVOID

    levels = [flag["level"] for flag in flags]
    if "high" in levels:
        return VERDICT_AVOID
    if "moderate" in levels or potential_concern:
        return VERDICT_CAUTION
    return VERDICT_OK


# ===============================================================
# GENERIC FALLBACK RESPONSE
# NOTE: CONCEPTUALLY belongs in ai_manager (build promts / fetch
# content rather than deciding) idk if we should move it or keep it here
# ===============================================================

def generate_generic_response_prompt(user_profile: dict) -> str:
    """should the response confidence be poor even after reprompt, build a
    prompt that ignores the original request food item and ask for food
    recos based on user profile and conditions
    """
    age = user_profile.get("age")
    gender = user_profile.get("gender")
    ethnicity = user_profile.get("ethnicity")
    country = user_profile.get("country")

    if "medical_conditions" not in user_profile:
        conditions = "not provided (unknown, NOT confirmed as none)"
    else:
        conditions = ", ".join(user_profile["medical_conditions"]) or "none reported"


    return (
        f"I am a {age}-year-old {ethnicity} {gender} from {country} with the following medical conditions: {conditions}. "
        f"What are the best foods I should eat given my medical conditions?"
    )
    

def generate_generic_response(user_profile: dict | None = None) -> dict:
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

NUTRIENT_LABELS = {
    "sodium_mg": ("Sodium", "mg"),
    "sugar_g": ("Sugar", "g"),
    "saturated_fat_g": ("Saturated fat", "g"),
    "trans_fat_g": ("Trans fat", "g"),
}


def format_result_for_user(result: dict) -> str:
    action = result["action"]

    if action == RESPONSE_REPROMPT:
        return ""  # nothing to show yet, main.py asks the AI again

    if action == RESPONSE_FALLBACK:
        return "We are unable to confidently determine whether this food suits you."

    lines = [f"VERDICT: {result['verdict'].upper()}"]

    if result["allergen_warning"]:
        lines += ["", result["allergen_warning"]]

    lines += ["", "Why:", result["reason"].strip()]

    nutrition = result["nutrition"]
    if nutrition:
        lines += ["", "Nutrition (per typical serving):"]
        for key, (label, unit) in NUTRIENT_LABELS.items():
            if key in nutrition:
                lines.append(f"  {label}: {nutrition[key]} {unit}")

    if result["nutrition_flags"]:
        lines += ["", "Watch out for your conditions:"]
        for flag in result["nutrition_flags"]:
            label, unit = NUTRIENT_LABELS.get(flag["nutrient"], (flag["nutrient"], ""))
            lines.append(f"  - {label} is {flag['level'].upper()} ({flag['value']} {unit})")

    return "\n".join(lines)


# ===================================================
# MAIN ENTRY POINT - the one function main.py needs to call
# ===================================================

def process_ai_response(ai_response: dict, user_profile: dict, attempt_number: int = 1) -> dict:
    """INPUT : ai_response  - the dict ai_manager produced, e.g.
                              {"status": "complete", "potential_concern": True,
                               "confidence_score": 90, "nutrition": {...},
                               "reason": "...", "information_needed": {}}
                              (None is accepted too: it means the AI failed)
               user_profile - the logged-in user's profile dict
               attempt_number - 1 on the first try, 2 after a reprompt
 
    OUTPUT: one dict, ready for io_manager to show the user:
        action           "accept" | "avoid" | "reprompt" | "fallback"
                         accept   -> show the assessment as normal
                         avoid    -> an allergen was found, show the warning
                         reprompt -> AI was not confident, ask it once more
                         fallback -> still not confident, send fallback_prompt
                                     to the AI and show that answer instead
        verdict          "Avoid" | "Caution" | "OK" (None if we could not judge)
        confidence_score 0.0 - 10.0
        potential_concern  the AI's own flag (None if the AI failed)
        reason           the AI's explanation, passed straight through
        nutrition        the AI's numbers (empty if none)
        nutrition_flags  nutrients over a threshold that matter for this user
        allergen_warning text to show, or None
        fallback_prompt  text to send to the AI when action is "fallback"
    """
    confidence_result = calculate_response_confidence(ai_response)
 
    reason = ""
    nutrition = {}
    if ai_response is not None:
        reason = ai_response.get("reason", "")
        nutrition = ai_response.get("nutrition", {})
 
    # 1. Allergens first: a match always wins, even if the AI was unsure.
    allergens_found = detect_allergens(reason) if reason else {}
 
    if allergens_found:
        action = RESPONSE_AVOID
    else:
        # 2. Otherwise, is the AI confident enough?
        action = evaluate_response_confidence(confidence_result, attempt_number)
 
    # 3. Only judge the food when we trust the answer (accept) or must warn (avoid)
    flags = []
    verdict = None
    if action in (RESPONSE_ACCEPT, RESPONSE_AVOID):
        conditions = user_profile.get("medical_conditions", [])
        flags = check_nutrition(nutrition, conditions)
        verdict = determine_verdict(
            flags, allergens_found, confidence_result["potential_concern"]
        )
 
    fallback_prompt = None
    if action == RESPONSE_FALLBACK:
        fallback_prompt = generate_generic_response_prompt(user_profile)
 
    return {
        "action": action,
        "verdict": verdict,
        "confidence_score": confidence_result["overall_score"],
        "potential_concern": confidence_result["potential_concern"],
        "reason": reason,
        "nutrition": nutrition,
        "nutrition_flags": flags,
        "allergen_warning": build_allergen_warning(allergens_found) if allergens_found else None,
        "fallback_prompt": fallback_prompt,
    }
    

# ===================================================
# TEMPORARY MOCK FUNCTIONS FOR TESTING PURPOSES
# ===================================================

if __name__ == "__main__":
    print("=" * 50)
    print("TEST 1: Normal Food (Heinz Beanz)")
    print("=" * 50)
    confidence_result = calculate_response_confidence(MOCK_AI_RESPONSE)
    action = evaluate_response_confidence(confidence_result, attempt_number=1)
    print(f"    Confidence score : {confidence_result['overall_score']} / 10")
    print(f"    Potential concern: {confidence_result['potential_concern']}")
    print(f"    Action           : {action.upper()}")
 
    '''No AI response at all (None)'''
    print("=" * 50)
    print("TEST: No AI response (None)")
    print("=" * 50)
    none_result = calculate_response_confidence(None)
    for attempt in (1, 2):
        none_action = evaluate_response_confidence(none_result, attempt_number=attempt)
        print(f"    Attempt {attempt} -> {none_action.upper()}")
 
    '''Mock Response Allergen Detection'''
    print("=" * 50)
    print("TEST 2: Allergen Food (Prawn Crackers)")
    print("=" * 50)
    found = detect_allergens(MOCK_AI_RESPONSE_ALLERGEN["reason"])
    if found:
        print(build_allergen_warning(found))
    else:
        print("No Allergens detected")
 
    '''Nutrition check: the AI's numbers vs thresholds.json'''
    print()
    print("=" * 50)
    print("TEST: Nutrition check (Heinz Beanz)")
    print("=" * 50)
    for label, conditions in [
        ("diabetes + high blood pressure", ["diabetes", "high blood pressure"]),
        ("no conditions", []),
    ]:
        flags = check_nutrition(MOCK_AI_RESPONSE["nutrition"], conditions)
        verdict = determine_verdict(flags, {}, MOCK_AI_RESPONSE["potential_concern"])
        print(f"    User: {label}")
        print(f"      Flags  : {flags}")
        print(f"      Verdict: {verdict}")
 
    '''End to end: AI dict in -> display dict out'''
    low_confidence = {**MOCK_AI_RESPONSE, "confidence_score": 30}
    scenarios = [
        ("Normal food, user has diabetes + high blood pressure", MOCK_AI_RESPONSE, 1),
        ("Allergen food (prawn crackers)", MOCK_AI_RESPONSE_ALLERGEN, 1),
        ("Low confidence, first try", low_confidence, 1),
        ("Low confidence, second try", low_confidence, 2),
        ("AI failed (None), second try", None, 2),
    ]
    for title, response, attempt in scenarios:
        print()
        print("=" * 50)
        print("END TO END:", title)
        print("=" * 50)
        output = process_ai_response(response, MOCK_USER_PROFILE, attempt)
        print(json.dumps(output, indent=2, ensure_ascii=False))