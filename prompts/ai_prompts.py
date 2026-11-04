import json

# =========== AI Response JSON Format ===========
RESPONSE_SCHEMA = {
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
        "nutrition": {
            "type": "object",
            "properties": {
                "sodium_mg": {"type": "number"},
                "sugar_g": {"type": "number"},
                "saturated_fat_g": {"type": "number"},
                "trans_fat_g": {"type": "number"}
            },
            "required": ["sodium_mg", "sugar_g", "saturated_fat_g", "trans_fat_g"],
        },
        "reason": {"type": "string"},
        "information_needed": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "required": [
        "status", "potential_concern", "confidence_score",
        "reason", "information_needed",
    ],
    "additionalProperties": False,
}

FOLLOW_UP_SCHEMA = {}


# =========== AI Response Validation ===========
EXPECTED_KEYS = set(RESPONSE_SCHEMA["properties"])

NUTRIENT_KEYS = {"sodium_mg", "sugar_g", "saturated_fat_g", "trans_fat_g"}


# =========== Prompt Builder Parts ===========
YOUR_PURPOSE = ""

ADHERE_TO_THESE_RULES = ""

WHEN_TO_FOLLOW_UP = ""

HOW_TO_FOLLOW_UP = ""

WHEN_TO_REPROMPT = ""

HOW_TO_REPROMPT = ""

USE_OPENFOODFACTS_DATA = ""

WHAT_IS_CONFIDENCE_SCORE = ""

DO_NOT_MAKE_ASSUMPTIONS = ""

HOW_TO_DEAL_WITH_CHAT_HISTORY = ""

HOW_TO_DEAL_WITH_FALLBACK_PROMPT = ""

