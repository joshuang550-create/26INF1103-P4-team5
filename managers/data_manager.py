import os
import csv
import json
import pathlib
from contextlib import suppress

from cryptography.fernet import Fernet, InvalidToken

from models.user_profile import UserProfile
from models.errors import DataError, ConfigurationError

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

_REQUIRED = object()


class DataManager:
    def __init__(self):
        self.__profiles_path = pathlib.Path(os.getenv("USER_PROFILES", str(BASE_DIR / "data" / "user_profiles.json")))
        self.__countries_path = pathlib.Path(os.getenv("COUNTRIES", str(BASE_DIR / "lookup" / "./countries.csv")))
        self.__ethnicities_path = pathlib.Path(os.getenv("ETHNICITIES", str(BASE_DIR / "lookup" / "./ethnicities.csv")))
        self.__chats_path = pathlib.Path(os.getenv("CHATS", str(BASE_DIR / "data" / "./chats.json")))
        self.__thresholds_path = pathlib.Path(os.getenv("THRESHOLDS", str(BASE_DIR / "lookup" / "./thresholds.json")))
        self.__allergens_path = pathlib.Path(os.getenv("ALLERGENS", str(BASE_DIR / "lookup" / "./allergens.json")))
        self.__encrypted_api_key = pathlib.Path(os.getenv("ENCRYPTED_API_KEY", str(BASE_DIR / "./encrypted_api_key.bin")))

    # =========== Private Helpers ===========
    @staticmethod
    def _read_json(path, default=_REQUIRED): # profile and chat can be {} but lookups must exist
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as error:
            if default is _REQUIRED:
                raise ConfigurationError(f"A required file is missing: {path.name}") from error
            return default
        except (json.JSONDecodeError, UnicodeDecodeError) as error: # as its own error so that returning {} would let the next save overwrite every stored profile
            raise DataError(f"{path.name} could not be read. Nothing has been changed.") from error
        except OSError as error:
            raise DataError(f"{path.name} could not be read.") from error

    @staticmethod
    def _write_json(path, data, indent):
        temp = path.with_name(path.name + ".tmp") # write to a temp file first, so a crash mid-write cannot leave a half-written (corrupted) file
        try:
            path.parent.mkdir(parents=True, exist_ok=True) # creates the directory leading up to path if it doesnt exist
            with temp.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=indent)
            temp.replace(path)
        except OSError as error:
            with suppress(OSError):
                temp.unlink(missing_ok=True) # remove the half-written temp file
            raise DataError("Could not save data. Check that there is free space and permission to write.") from error

    @staticmethod
    def _csv_contains(path, value):
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                return any(row and row[0].lower() == value.lower() for row in csv.reader(file))
        except FileNotFoundError as error:
            raise ConfigurationError(f"A required file is missing: {path.name}") from error
        except (OSError, UnicodeDecodeError) as error:
            raise DataError(f"{path.name} could not be read.") from error

    def _read_lookup(self, path, key): # lookup json files must exist and contain their top-level key
        data = self._read_json(path)
        if not isinstance(data, dict) or key not in data:
            raise ConfigurationError(f"{path.name} is not in the expected format.")
        return data[key]

    # =========== Profile Methods ===========
    def login(self, username, password):
        username = username.strip().lower()
        for profile in self._read_json(self.__profiles_path, {}).values():
            if profile.get("username", "").strip().lower() != username:
                continue
            try:
                profile = UserProfile.from_dict(profile)
            except (ValueError, TypeError, AttributeError) as error:
                raise DataError("The saved profile for this username is corrupted and cannot be loaded.") from error
            if profile.verify_password(password):
                return profile
        return None # unknown username or wrong password, cannot log in. The caller decides what to raise
    
    def save_profile(self, profile):
        record = profile.to_dict()
        profiles = self._read_json(self.__profiles_path, {})
        profiles[record["username"]] = record # if username already exists, overwrite, else, create new
        self._write_json(self.__profiles_path, profiles, indent=4)

    def delete_profile(self, profile):
        record = profile.to_dict()
        profiles = self._read_json(self.__profiles_path, )
        profiles.pop(record["username"], None) # deletes the key value pair by the key, key is username
        self._write_json(self.__profiles_path, profiles, indent=4)

    def is_username_taken(self, username):
        username = username.strip().lower()
        return any(record.get("username", "").strip().lower() == username for record in self._read_json(self.__profiles_path, {}).values()) # returns True / False

    # =========== Lookup Methods ===========
    def is_valid_country(self, country):
        return self._csv_contains(self.__countries_path, country) # returns True / False

    def is_valid_ethnicity(self, ethnicity):
        return self._csv_contains(self.__ethnicities_path, ethnicity) # returns True / False

    def get_thresholds(self):
        return self._read_lookup(self.__thresholds_path, "nutrients") # returns: {'sodium_mg': {'moderate': 300, 'high': 600, 'relevant_conditions': ['hypertension', 'blood pressure', 'kidney']}, 'sugar_g': {'moderate': 10, 'high': 22.5, 'relevant_conditions': ['diabet']}, 'saturated_fat_g': {'moderate': 1.5, 'high': 5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}, 'trans_fat_g': {'moderate': 0.1, 'high': 0.5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}}

    def get_allergens(self):
        return self._read_lookup(self.__allergens_path, "allergen_synonyms") # returns {'shellfish_crustacean': ['shrimp', 'crab', 'prawn', 'lobster'], 'shellfish_mollusk': ['clam', 'mussel', 'oyster', 'scallop']}

    # =========== AI Support ===========
    def get_api_key(self):
        secret = os.getenv("FERNET_SECRET_KEY")
        if not secret:
            raise ConfigurationError("The environment variable FERNET_SECRET_KEY is not set.")
        try:
            return Fernet(secret).decrypt(self.__encrypted_api_key.read_bytes()).decode()
        except FileNotFoundError as error:
            raise ConfigurationError("The encrypted API key file is missing.") from error
        except (InvalidToken, ValueError) as error: # wrong secret key or wrong format
            raise ConfigurationError("The secret key could not decrypt the API key. Check FERNET_SECRET_KEY.") from error

    def get_chat_history(self, username):
        return self._read_json(self.__chats_path, {}).get(str(username), None) # returns: [{'role': 'user', 'text': 'Give a risk assessment for this food: Chocolate Protein Bar\nIngredients: whey protein, maltitol, peanuts, caffeine', 'time': 1791527388}, {'role': 'model', 'text': '{\n  "status": "complete",\n  "potential_concern": true,\n  "reason": "The chocolate protein bar contains caffeine, which can potentially raise blood pressure, a concern given your medical history of high blood pressure. Additionally, maltitol is a sugar alcohol that can sometimes cause gastrointestinal distress, and the peanuts are a hard texture that might aggravate TMJ symptoms.",\n  "information_needed": []\n}', 'time': 1791527388}]

    def save_chat_history(self, username, history):
        all_history = self._read_json(self.__chats_path, {})
        all_history[str(username)] = history # history is a list of dicts
        self._write_json(self.__chats_path, all_history, indent=4)

    def delete_chat_history(self, username):
        history = self._read_json(self.__chats_path, {})
        history.pop(str(username), None) # if username has no chat history, does nothing and continues as per normal
        self._write_json(self.__chats_path, history, indent=4)
