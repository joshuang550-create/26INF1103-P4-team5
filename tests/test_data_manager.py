"""Persistence: round trips, missing files, corrupted files, unwritable locations, API key handling."""
import json
import os
import pathlib
import unittest
from unittest import mock

from cryptography.fernet import Fernet

from managers.data_manager import DataManager
from models.errors import ConfigurationError, DataError
from tests.helpers import TempDataTestCase, make_profile


class ProfilePersistenceTests(TempDataTestCase):
    def test_save_then_login_round_trip(self):
        self.data.save_profile(make_profile(["hypertension"]))
        loaded = self.data.login("tester", "pw")
        self.assertEqual((loaded.username, loaded.age, loaded.medical_conditions), ("tester", 30, ["hypertension"]))

    def test_login_is_case_insensitive_on_username_but_checks_password(self):
        self.data.save_profile(make_profile())
        self.assertIsNotNone(self.data.login("  TESTER ", "pw"))
        self.assertIsNone(self.data.login("tester", "wrong"))
        self.assertIsNone(self.data.login("ghost", "pw"))

    def test_saving_again_overwrites_instead_of_duplicating(self):
        profile = make_profile()
        self.data.save_profile(profile)
        profile.age = 40
        self.data.save_profile(profile)
        with open(self.profiles_path, encoding="utf-8") as file:
            self.assertEqual(len(json.load(file)), 1)
        self.assertEqual(self.data.login("tester", "pw").age, 40)

    def test_delete_profile(self):
        profile = make_profile()
        self.data.save_profile(profile)
        self.data.delete_profile(profile)
        self.assertFalse(self.data.is_username_taken("tester"))

    def test_deleting_an_unknown_profile_does_nothing(self):
        self.data.delete_profile(make_profile(username="ghost"))

    def test_username_taken_ignores_case_and_spaces(self):
        self.data.save_profile(make_profile())
        self.assertTrue(self.data.is_username_taken(" Tester "))
        self.assertFalse(self.data.is_username_taken("other"))

    def test_missing_profiles_file_is_treated_as_no_users(self):
        self.assertFalse(os.path.exists(self.profiles_path))
        self.assertIsNone(self.data.login("tester", "pw"))
        self.assertFalse(self.data.is_username_taken("tester"))

    def test_first_save_creates_missing_folders(self):
        nested = os.path.join(self.tmp, "a", "b", "profiles.json")
        with mock.patch.dict(os.environ, {"USER_PROFILES": nested}):
            DataManager().save_profile(make_profile())
        self.assertTrue(os.path.exists(nested))

    def test_no_temp_file_is_left_behind(self):
        self.data.save_profile(make_profile())
        self.assertEqual(os.listdir(self.tmp), ["user_profiles.json"])


class CorruptFileTests(TempDataTestCase):
    def write(self, path, text):
        pathlib.Path(path).write_text(text, encoding="utf-8")

    def test_corrupt_profiles_file_raises_data_error(self):
        self.write(self.profiles_path, "{this is not json")
        for call in (lambda: self.data.login("tester", "pw"), lambda: self.data.is_username_taken("tester")):
            with self.assertRaises(DataError):
                call()

    def test_corrupt_file_is_not_overwritten_by_a_save(self):
        self.write(self.profiles_path, "{this is not json")
        with self.assertRaises(DataError):
            self.data.save_profile(make_profile())
        self.assertEqual(pathlib.Path(self.profiles_path).read_text(encoding="utf-8"), "{this is not json")  # other users' data survives

    def test_binary_garbage_raises_data_error(self):
        pathlib.Path(self.profiles_path).write_bytes(b"\xff\xfe\x00\x81garbage")
        with self.assertRaises(DataError):
            self.data.login("tester", "pw")

    def test_corrupt_chat_file_raises_data_error(self):
        self.write(self.chats_path, "[[[")
        with self.assertRaises(DataError):
            self.data.get_chat_history("tester")

    def test_single_damaged_profile_is_reported_not_crashed(self):
        self.write(self.profiles_path, json.dumps({"tester": {"username": "tester", "password_hash": "x", "age": "old"}}))
        with self.assertRaises(DataError):
            self.data.login("tester", "pw")

    def test_unwritable_location_raises_data_error(self):
        blocker = pathlib.Path(self.tmp) / "blocker"
        blocker.write_text("i am a file, not a folder")
        with mock.patch.dict(os.environ, {"USER_PROFILES": str(blocker / "sub" / "profiles.json")}):
            manager = DataManager()
        with self.assertRaises(DataError):
            manager.save_profile(make_profile())


class LookupFileTests(TempDataTestCase):
    def manager_with(self, **env):
        with mock.patch.dict(os.environ, env):
            return DataManager()

    def test_bundled_lookup_files_load(self):
        thresholds = self.data.get_thresholds()
        self.assertEqual(set(thresholds["sodium_mg"]), {"moderate", "high", "relevant_conditions"})
        self.assertIsInstance(self.data.get_allergens(), dict)
        self.assertIn("Hypertension", self.data.get_conditions())

    def test_missing_required_lookup_file_raises_configuration_error(self):
        manager = self.manager_with(THRESHOLDS=os.path.join(self.tmp, "nope.json"), COUNTRIES=os.path.join(self.tmp, "nope.csv"))
        with self.assertRaises(ConfigurationError):
            manager.get_thresholds()
        with self.assertRaises(ConfigurationError):
            manager.is_valid_country("Singapore")

    def test_lookup_json_with_wrong_shape_raises_configuration_error(self):
        path = os.path.join(self.tmp, "thresholds.json")
        pathlib.Path(path).write_text(json.dumps({"wrong_key": {}}), encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            self.manager_with(THRESHOLDS=path).get_thresholds()

    def test_corrupt_lookup_json_raises_data_error(self):
        path = os.path.join(self.tmp, "allergens.json")
        pathlib.Path(path).write_text("{{{", encoding="utf-8")
        with self.assertRaises(DataError):
            self.manager_with(ALLERGENS=path).get_allergens()

    def test_lookup_checks_are_case_insensitive(self):
        self.assertTrue(self.data.is_valid_country("SINGAPORE"))
        self.assertTrue(self.data.is_valid_ethnicity("chinese"))
        self.assertFalse(self.data.is_valid_country(""))


class ChatHistoryTests(TempDataTestCase):
    def test_unknown_user_has_no_history(self):
        self.assertIsNone(self.data.get_chat_history("tester"))

    def test_save_get_delete(self):
        history = [{"role": "user", "text": "hi", "time": 1}]
        self.data.save_chat_history("tester", history)
        self.data.save_chat_history("other", [])
        self.assertEqual(self.data.get_chat_history("tester"), history)
        self.data.delete_chat_history("tester")
        self.assertIsNone(self.data.get_chat_history("tester"))
        self.assertEqual(self.data.get_chat_history("other"), [])

    def test_deleting_missing_history_is_harmless(self):
        self.data.delete_chat_history("nobody")


class ApiKeyTests(TempDataTestCase):
    def setUp(self):
        super().setUp()
        self.secret = Fernet.generate_key().decode()
        self.key_path = os.path.join(self.tmp, "encrypted_api_key.bin")
        pathlib.Path(self.key_path).write_bytes(Fernet(self.secret).encrypt(b"fake-api-key-123"))

    def manager(self, key_path=None):
        with mock.patch.dict(os.environ, {"ENCRYPTED_API_KEY": key_path or self.key_path}):
            return DataManager()

    def test_key_is_decrypted(self):
        with mock.patch.dict(os.environ, {"FERNET_SECRET_KEY": self.secret}):
            self.assertEqual(self.manager().get_api_key(), "fake-api-key-123")

    def test_missing_secret_raises_configuration_error(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("FERNET_SECRET_KEY", None)
            with self.assertRaises(ConfigurationError):
                self.manager().get_api_key()

    def test_wrong_secret_raises_configuration_error(self):
        with mock.patch.dict(os.environ, {"FERNET_SECRET_KEY": Fernet.generate_key().decode()}):
            with self.assertRaises(ConfigurationError):
                self.manager().get_api_key()

    def test_malformed_secret_raises_configuration_error(self):
        with mock.patch.dict(os.environ, {"FERNET_SECRET_KEY": "not-a-valid-fernet-key"}):
            with self.assertRaises(ConfigurationError):
                self.manager().get_api_key()

    def test_missing_key_file_raises_configuration_error(self):
        with mock.patch.dict(os.environ, {"FERNET_SECRET_KEY": self.secret}):
            with self.assertRaises(ConfigurationError):
                self.manager(os.path.join(self.tmp, "missing.bin")).get_api_key()


if __name__ == "__main__":
    unittest.main()
