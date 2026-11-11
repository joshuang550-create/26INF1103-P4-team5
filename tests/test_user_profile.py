"""UserProfile and MedicalConditions: validation and behaviour."""
import unittest

from models.errors import InvalidInputError
from models.user_profile import MedicalConditions, UserProfile
from tests.helpers import make_profile


class ValidationTests(unittest.TestCase):
    def test_age_rules(self):
        for bad in (0, -5, 121, 30.5, "30", None):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                UserProfile.validate_age(bad)
        self.assertEqual(UserProfile.validate_age(120), 120)

    def test_height_and_weight_rules(self):
        for bad in (0, -1, 261, "170", None):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                UserProfile.validate_height(bad)
        for bad in (0, -1, 501, "70", None):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                UserProfile.validate_weight(bad)
        self.assertEqual(UserProfile.validate_height(260), 260)
        self.assertEqual(UserProfile.validate_weight(500), 500)

    def test_gender_is_normalised_and_restricted(self):
        self.assertEqual(UserProfile.validate_gender(" Female "), "female")
        for bad in ("other", "", None, 1):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                UserProfile.validate_gender(bad)

    def test_username_must_be_non_empty_text(self):
        self.assertEqual(UserProfile.validate_username("  sam "), "sam")
        for bad in ("", "   ", None, 5):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                UserProfile.validate_username(bad)

    def test_setters_validate(self):
        profile = make_profile()
        with self.assertRaises(InvalidInputError):
            profile.age = 0
        profile.height = 180
        self.assertEqual(profile.height, 180)


class BehaviourTests(unittest.TestCase):
    def test_password_is_hashed_and_verifiable(self):
        profile = make_profile(plain_password="s3cret")
        self.assertNotIn("s3cret", str(profile.to_dict()))
        self.assertTrue(profile.verify_password("s3cret"))
        self.assertFalse(profile.verify_password("S3cret"))

    def test_bmi(self):
        self.assertEqual(make_profile(height=175.0, weight=70.0).bmi, 22.86)

    def test_dict_round_trip(self):
        profile = make_profile(["hypertension", "peanut allergy"])
        copy = UserProfile.from_dict(profile.to_dict())
        self.assertEqual(copy.to_dict(), profile.to_dict())

    def test_from_dict_rejects_damaged_data(self):
        with self.assertRaises(InvalidInputError):
            UserProfile.from_dict({"username": "x", "age": 30})

    def test_allergies_only_returns_allergy_conditions(self):
        profile = make_profile()
        profile.add_medical_conditions(["Hypertension", "Shrimp Allergy", "Peanut ALLERGY"])
        self.assertEqual(profile.allergies, ["shrimp allergy", "peanut allergy"])

    def test_condition_keyword_matching(self):
        profile = make_profile(["Type 2 Diabetes"])
        self.assertTrue(profile.has_condition_matching(["diabet"]))
        self.assertFalse(profile.has_condition_matching(["hypertension"]))

    def test_conditions_returned_are_a_copy(self):
        profile = make_profile(["hypertension"])
        profile.medical_conditions.append("hacked")
        self.assertEqual(profile.medical_conditions, ["hypertension"])


class MedicalConditionsTests(unittest.TestCase):
    def test_conditions_are_trimmed_and_lowercased(self):
        conditions = MedicalConditions()
        conditions.add_conditions(["  High Blood Pressure "])
        self.assertEqual(conditions.to_list(), ["high blood pressure"])

    def test_too_short_condition_is_rejected_and_nothing_is_added(self):
        conditions = MedicalConditions(["asthma"])
        with self.assertRaises(InvalidInputError):
            conditions.add_conditions(["gout", "a"])
        self.assertEqual(conditions.to_list(), ["asthma"])

    def test_remove_by_position(self):
        conditions = MedicalConditions(["a1", "b2", "c3", "d4"])
        conditions.remove_conditions([0, 2])
        self.assertEqual(conditions.to_list(), ["b2", "d4"])
        self.assertEqual(len(conditions), 2)


if __name__ == "__main__":
    unittest.main()
