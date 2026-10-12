


import os
import json
import math

from google import genai
from google.genai import errors
import httpx

import data_manager

AI_MODEL = "gemini-3.5-flash-lite"
SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["complete", "needs_follow_up"],
        },
        "potential_concern": {
            "type": "boolean",
            "description": "Whether a possible concern was identified. False is not a safety guarantee.",
        },
        "confidence_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": (
                "Self-reported confidence in the assessment of this food for this user, "
                "based on the available relevant evidence, from 0 to 100. "
                "Not a calibrated probability of correctness or food safety."
            ),
        },
        "reason": {"type": "string"},
        "information_needed": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "status", "potential_concern", "confidence_score",
        "reason", "information_needed",
    ],
    "additionalProperties": False,
}
EXPECTED_KEYS = set(SCHEMA["properties"])
NUTRIENT_KEYS = {"sodium_mg", "sugar_g", "saturated_fat_g", "trans_fat_g"}


def validate_ai_response(data):
    """Check 2: exact keys and the correct type for every field."""
    if not isinstance(data, dict) or set(data) != EXPECTED_KEYS:
        return False

    if not (
        isinstance(data["status"], str)                       # string
        and data["status"] in ("complete", "needs_follow_up")
        and isinstance(data["potential_concern"], bool)       # boolean
        and type(data["confidence_score"]) is int             # integer (not 90.0, not True)
        and 0 <= data["confidence_score"] <= 100
        and isinstance(data["reason"], str)                   # string, not empty
        and data["reason"].strip() != ""
        and isinstance(data["nutrition"], dict)
        and set(data["nutrition"]) == NUTRIENT_KEYS           # sodium_mg, sugar_g, saturated_fat_g, trans_fat_g
        and all(is_number(v) and v >= 0 for v in data["nutrition"].values())   # numbers, not "10 g"
        and isinstance(data["information_needed"], list)
    ):
        return False

    # Follow-up consistency (same rules as before, items are {"key", "type"})
    seen = set()
    for item in data["information_needed"]:
        if not (
            isinstance(item, dict)
            and set(item) == {"key", "type"}
            and isinstance(item["key"], str) and item["key"].strip()
            and item["type"] in ("string", "int", "float")
            and item["key"] not in seen
        ):
            return False
        seen.add(item["key"])

    if data["status"] == "complete":
        return data["information_needed"] == []
    return len(data["information_needed"]) > 0


def generate_first_prompt(user_profile):
    bmi = round(user_profile["weight"] / ((user_profile["height"] / 100) ** 2), 1)

    if "medical_conditions" not in user_profile:
        conditions = "not provided (unknown, NOT confirmed as none)"

    else:
        conditions = ", ".join(user_profile["medical_conditions"]) or "none reported"

    return (
    "You analyse food products for possible health concerns. Do not make a medical "
    "diagnosis. Return structured output only.\n\n"
    "User profile:\n"
    f"- Age: {user_profile['age']}\n"
    f"- Gender: {user_profile['gender']}\n"
    f"- Ethnicity: {user_profile['ethnicity']}\n"
    f"- Country: {user_profile['country']}\n"
    f"- Height: {user_profile['height']} cm\n"
    f"- Weight: {user_profile['weight']} kg\n"
    f"- BMI: {bmi}\n"
    f"- Medical conditions: {conditions}\n\n"
    "Tailor each assessment to this profile and to everything earlier in this "
    "conversation (previous foods and any information the user gave). If you need more "
    "information about the user, set status to 'needs_follow_up' and list each piece of "
    "information in information_needed; the user will reply with a JSON object where "
    "each key is one of your requests, filled in. Otherwise set status to 'complete' and "
    "leave information_needed empty. Always fill in the nutrition estimates "
            "(sodium in mg, sugar in g, saturated fat in g, trans fat in g)."
        )


def generate_more_info_prompt(more_info_input):
    """Turn the filled-in dict, e.g. {"alcohol intake": "2 drinks/week"}, into a prompt string."""
    lines = [f"- {key}: {value}" for key, value in more_info_input.items()]
    return (
        "Here is the additional information you asked for:\n"
        + "\n".join(lines)
        + "\n\nUse it to reassess the same food. Update the potential concern, reason, "
        "confidence and nutrition values. If you still need more information, set status "
        "to 'needs_follow_up' and list only what is still missing; otherwise set status "
        "to 'complete' and leave information_needed empty."
    )







def send_prompt_to_ai(user_profile, prompt_string): # also has error handling.
    # has to be usable for both first prompt and more info prompt.

    data_manager.get_ai_api_key()

    history = data_manager.load_chat_history() # loads a dictionary of all user's chat histories
    user_history = history.setdefault(user_profile.get("username", ""), []) # if user has no history, creates an empty list as new history

    # print user_history see what datatype it is. Must be a list [].

    try:
        client = genai.Client()
        chat = client.chats.create(model=AI_MODEL, history=user_history)
        response = chat.send_message(prompt_string)

    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pass  # call io_manager.print_api_error_message(e)   maybe print that internet connection unstable, could not reach google, try again later. or smth.

    except errors.APIError as e:
        if e.code == 400:
            print(f"API Error 400 (Bad Request): Check your model name '{AI_MODEL}' or empty prompt string. Message: {e.message}") # see how to handle this, not user fault.
        
        elif e.code == 401:
            print(f"API Error 401 (Unauthorized): Check if your API Key is valid and exported correctly. Message: {e.message}") # call io_manager.print_api_error_message(e)
        
        elif e.code == 403:
            print(f"API Error 403 (Forbidden): Permission denied or regional restriction. Message: {e.message}") # call io_manager.print_api_error_message(e)
        
        elif e.code == 429:
            print(f"API Error 429 (Rate Limit): You are making too many requests or out of credits. Message: {e.message}") # call io_manager.print_api_error_message(e)
        
        elif e.code in [500, 503]:
            print(f"API Error {e.code} (Server Error): Google's servers are temporarily down. Message: {e.message}") # call io_manager.print_api_error_message(e)

    except Exception as e:
        pass  # call io_manager.print_api_error_message(e)       say unexpected error?

    history[user_profile.get("username", "")] = user_history
    data_manager.save_chats(history)
    
    return response



