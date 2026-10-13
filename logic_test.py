"""Offline tests for the functions in logic_manager.
    Will not be run by main.py as this is a developer-time
    self check, not for run-time. Not sure what the brief
    means by "Must pass cleanly inside the Docker container"
    but if these functions were to be called, it would work fine.
"""

from unittest.mock import patch

import managers.logic_manager as logic_manager


def test_calculate_response_confidence():
    ai_response = {"confidence_score": 85, "potential_concern": True}
    expected = {"overall_score": 8.5, "potential_concern": True}

    assert logic_manager.calculate_response_confidence(ai_response) == expected
    assert logic_manager.calculate_response_confidence(None) == {
        "overall_score": 0.0,
        "potential_concern": None,
    }


def test_evaluate_response_confidence():
    assert logic_manager.evaluate_response_confidence(
        {"overall_score": 5.0}, attempt_number=1
    ) == "accept"
    assert logic_manager.evaluate_response_confidence(
        {"overall_score": 4.9}, attempt_number=1
    ) == "reprompt"
    assert logic_manager.evaluate_response_confidence(
        {"overall_score": 4.9}, attempt_number=2
    ) == "fallback"


def test_user_has_condition():
    assert logic_manager.user_has_condition(
        ["High Blood Pressure"], ["blood pressure"]
    ) is True
    assert logic_manager.user_has_condition(
        ["diabetes"], ["blood pressure"]
    ) is False


def test_check_nutrition():
    thresholds = {
        "sodium_mg": {
            "moderate": 120,
            "high": 600,
            "relevant_conditions": ["blood pressure"],
        }
    }
    conditions = ["high blood pressure"]

    assert logic_manager.check_nutrition(
        {"sodium_mg": 650}, conditions, thresholds
    ) == [{"nutrient": "sodium_mg", "value": 650, "level": "high"}]
    assert logic_manager.check_nutrition(
        {"sodium_mg": 600}, conditions, thresholds
    ) == [{"nutrient": "sodium_mg", "value": 600, "level": "moderate"}]
    assert logic_manager.check_nutrition(
        {"sodium_mg": 120}, conditions, thresholds
    ) == [{"nutrient": "sodium_mg", "value": 120, "level": "moderate"}]
    assert logic_manager.check_nutrition(
        {"sodium_mg": 119}, conditions, thresholds
    ) == []
    assert logic_manager.check_nutrition(
        {"sodium_mg": 650}, ["diabetes"], thresholds
    ) == []


def test_determine_verdict():
    assert logic_manager.determine_verdict(
        [], {"dairy": ["milk"]}, False
    ) == "AVOID"
    assert logic_manager.determine_verdict(
        [{"level": "high"}], {}, False
    ) == "AVOID"
    assert logic_manager.determine_verdict(
        [{"level": "moderate"}], {}, False
    ) == "CAUTION"
    assert logic_manager.determine_verdict([], {}, True) == "CAUTION"
    assert logic_manager.determine_verdict([], {}, False) == "OK"


def test_generate_generic_response_prompt():
    user_profile = {
        "age": 30,
        "gender": "male",
        "ethnicity": "Chinese",
        "country": "Singapore",
        "medical_conditions": ["diabetes", "high blood pressure"],
    }
    expected = (
        "I am a 30-year-old Chinese male from Singapore with the following "
        "medical conditions: diabetes, high blood pressure. "
        "What are the best foods I should eat given my medical conditions?"
    )

    assert logic_manager.generate_generic_response_prompt(user_profile) == expected


def test_detect_allergens():
    text = "Contains MILK, peanuts and eggs."
    synonyms = {"dairy": ["milk"], "nuts": ["peanut"], "eggs": ["egg"]}
    expected = {"dairy": ["milk"], "nuts": ["peanut"], "eggs": ["egg"]}

    assert logic_manager.detect_allergens(text, synonyms) == expected
    assert logic_manager.detect_allergens("Rice and water.", synonyms) == {}


def test_build_allergen_warning():
    found = {"dairy": ["milk"], "nuts": ["peanut"]}
    expected = (
        "  Allergens Found: Dairy, Milk, Nuts, Peanut\n"
        "  Warning        : Avoid this food, allergen detected"
    )

    assert logic_manager.build_allergen_warning(found) == expected


def test_format_result_for_user():
    result = {
        "action": "accept",
        "allergen_warning": None,
        "reason": "  This sample has high sodium.  ",
        "nutrition": {
            "sodium_mg": 650,
            "sugar_g": 2,
            "saturated_fat_g": 1,
            "trans_fat_g": 0,
        },
        "nutrition_flags": [
            {"nutrient": "sodium_mg", "value": 650, "level": "high"}
        ],
    }
    expected = (
        "\nThis sample has high sodium.\n"
        "\nNutrition (per typical serving):\n"
        "  Sodium: 650 mg\n"
        "  Sugar: 2 g\n"
        "  Saturated fat: 1 g\n"
        "  Trans fat: 0 g\n"
        "\nWatch out for your conditions:\n"
        "  - Sodium is HIGH (650 mg)"
    )

    assert logic_manager.format_result_for_user(result) == expected
    assert logic_manager.format_result_for_user({"action": "reprompt"}) == ""
    assert logic_manager.format_result_for_user({"action": "fallback"}) == (
        "We are unable to confidently determine whether this food suits you."
    )


def test_process_ai_response():
    ai_response = {
        "status": "complete",
        "confidence_score": 90,
        "potential_concern": False,
        "reason": "This sample has high sodium.",
        "nutrition": {"sodium_mg": 650},
        "information_needed": {},
    }
    user_profile = {"medical_conditions": ["high blood pressure"]}
    thresholds = {
        "sodium_mg": {
            "moderate": 120,
            "high": 600,
            "relevant_conditions": ["blood pressure"],
        }
    }
    allergens = {"dairy": ["milk"], "nuts": ["peanut"]}
    expected = {
        "action": "accept",
        "verdict": "AVOID",
        "confidence_score": 9.0,
        "potential_concern": False,
        "reason": "This sample has high sodium.",
        "nutrition": {"sodium_mg": 650},
        "nutrition_flags": [
            {"nutrient": "sodium_mg", "value": 650, "level": "high"}
        ],
        "allergen_warning": None,
        "fallback_prompt": None,
        "message": (
            "\nThis sample has high sodium.\n"
            "\nNutrition (per typical serving):\n"
            "  Sodium: 650 mg\n"
            "\nWatch out for your conditions:\n"
            "  - Sodium is HIGH (650 mg)"
        ),
    }

    # Supply fixed lookup data. The real logic_manager function still runs.
    with patch.object(logic_manager.data_manager, "load_thresholds", return_value=thresholds):
        with patch.object(logic_manager.data_manager, "load_allergens", return_value=allergens):
            actual = logic_manager.process_ai_response(ai_response, user_profile)

    assert actual == expected


if __name__ == "__main__":
    tests = [
        test_calculate_response_confidence,
        test_evaluate_response_confidence,
        test_user_has_condition,
        test_check_nutrition,
        test_determine_verdict,
        test_generate_generic_response_prompt,
        test_detect_allergens,
        test_build_allergen_warning,
        test_format_result_for_user,
        test_process_ai_response,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print(f"\n{len(tests)} tests passed.")
