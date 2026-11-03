import os
import csv
import json
import pathlib

from cryptography.fernet import Fernet

from models.user_profile import UserProfile

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


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
    def _read_json(self, path):
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path, data, indent):
        path.parent.mkdir(parents=True, exist_ok=True) # creates the directory leading up to path if it doesnt exist
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=indent)

    def _csv_contains(self, path, value):
        with path.open("r", encoding="utf-8", newline="") as file:
            return any(row and row[0].lower() == value.lower() for row in csv.reader(file))

    # =========== Profile Methods ===========
    def login(self, username, password):
        username = username.strip().lower()
        for profile in self._read_json(self.__profiles_path).values():
            if profile.get("username", "").strip().lower() != username:
                continue
            try:
                profile = UserProfile.from_dict(profile)
            except (KeyError, ValueError):
                return None # corrupted profile in json, cannot log in
            if profile.verify_password(password):
                return profile
        return None # wrong password, cannot log in
    
    def save_profile(self, profile):
        profile = profile.to_dict()
        profiles = self._read_json(self.__profiles_path)
        profiles[str(profile.get("username", str(profile["username"])))] = profile # if profile exists, overwrite. else create new.
        self._write_json(self.__profiles_path, profiles, indent=4)

    def delete_profile(self, username):
        profiles = self._read_json(self.__profiles_path)
        profiles.pop(str(username), None) # deletes the key value pair by the key, key is username
        self._write_json(self.__profiles_path, profiles, indent=4)

    def is_username_taken(self, username):
        username = username.strip().lower()
        return any(record.get("username", "").strip().lower() == username for record in self._read_json(self.__profiles_path).values()) # returns True / False

    # =========== Lookup Methods ===========
    def is_valid_country(self, country):
        return self._csv_contains(self.__countries_path, country) # returns True / False

    def is_valid_ethnicity(self, ethnicity):
        return self._csv_contains(self.__ethnicities_path, ethnicity) # returns True / False

    def get_thresholds(self):
        return self._read_json(self.__thresholds_path) # returns: {'nutrients': {'sodium_mg': {'moderate': 300, 'high': 600, 'relevant_conditions': ['hypertension', 'blood pressure', 'kidney']}, 'sugar_g': {'moderate': 10, 'high': 22.5, 'relevant_conditions': ['diabet']}, 'saturated_fat_g': {'moderate': 1.5, 'high': 5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}, 'trans_fat_g': {'moderate': 0.1, 'high': 0.5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}}}

    def get_allergens(self):
        return self._read_json(self.__allergens_path) # returns {'allergen_synonyms': {'shellfish_crustacean': ['shrimp', 'crab', 'prawn', 'lobster'], 'shellfish_mollusk': ['clam', 'mussel', 'oyster', 'scallop']}}

    # =========== AI Support ===========
    def get_api_key(self):
        secret = os.getenv("FERNET_SECRET_KEY")
        if not secret:
            raise ValueError("Environment variable FERNET_SECRET_KEY is not set.")
        return Fernet(secret).decrypt(self.__encrypted_api_key.read_bytes()).decode()

    def get_chat_history(self, username):
        return self._read_json(self.__chats_path).get(str(username), None) # returns: [{'role': 'user', 'text': 'Give a risk assessment for this food: Chocolate Protein Bar\nIngredients: whey protein, maltitol, peanuts, caffeine', 'time': 1791527388}, {'role': 'model', 'text': '{\n  "status": "complete",\n  "potential_concern": true,\n  "reason": "The chocolate protein bar contains caffeine, which can potentially raise blood pressure, a concern given your medical history of high blood pressure. Additionally, maltitol is a sugar alcohol that can sometimes cause gastrointestinal distress, and the peanuts are a hard texture that might aggravate TMJ symptoms.",\n  "information_needed": []\n}', 'time': 1791527388}]

    def save_chat_history(self, username, history):
        all_history = self._read_json(self.__chats_path)
        all_history[str(username)] = history # history is a list of dicts
        self._write_json(self.__chats_path, all_history, indent=4)

    def delete_chat_history(self, username):
        history = self._read_json(self.__chats_path)
        history.pop(str(username), None) # if username has no chat history, does nothing and continues as per normal
        self._write_json(self.__chats_path, history, indent=4)



# dataM = DataManager()

# profile = dataM.login("ride", "ride")

# print(dataM.is_username_taken("mary"))

# dataM.save_profile(profile)
# print("saved")

# dataM.delete_profile(profile.username)
# print("deleted")

# print(dataM.get_api_key()) # returns: AQ.Ab8RN6LTLlp3LMUyXaJ3Lw4iJgASqDBH-Wd7ATwaNcUqmYOM_w

# print(dataM.is_valid_country("singapore"))
# print(dataM.is_valid_ethnicity("chinese"))

# print(dataM.get_thresholds()) # returns: {'nutrients': {'sodium_mg': {'moderate': 300, 'high': 600, 'relevant_conditions': ['hypertension', 'blood pressure', 'kidney']}, 'sugar_g': {'moderate': 10, 'high': 22.5, 'relevant_conditions': ['diabet']}, 'saturated_fat_g': {'moderate': 1.5, 'high': 5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}, 'trans_fat_g': {'moderate': 0.1, 'high': 0.5, 'relevant_conditions': ['cardiovascular', 'heart', 'cholesterol']}}}
# print(dataM.get_allergens()) # returns {'allergen_synonyms': {'shellfish_crustacean': ['shrimp', 'crab', 'prawn', 'lobster'], 'shellfish_mollusk': ['clam', 'mussel', 'oyster', 'scallop']}}

# print(dataM.get_chat_history("mary")) # returns [{'role': 'user', 'text': 'Give a risk assessment for this food: Chocolate Protein Bar\nIngredients: whey protein, maltitol, peanuts, caffeine', 'time': 1791527388}, {'role': 'model', 'text': '{\n  "status": "complete",\n  "potential_concern": true,\n  "reason": "The chocolate protein bar contains caffeine, which can potentially raise blood pressure, a concern given your medical history of high blood pressure. Additionally, maltitol is a sugar alcohol that can sometimes cause gastrointestinal distress, and the peanuts are a hard texture that might aggravate TMJ symptoms.",\n  "information_needed": []\n}', 'time': 1791527388}]

# dataM.save_chat_history("mary", [{'role': 'user', 'text': 'Give a risk assessment for this food: Chocolate Protein Bar\nIngredients: whey protein, maltitol, peanuts, caffeine', 'time': 1791527388}, {'role': 'model', 'text': '{\n  "status": "complete",\n  "potential_concern": true,\n  "reason": "The chocolate protein bar contains caffeine, which can potentially raise blood pressure, a concern given your medical history of high blood pressure. Additionally, maltitol is a sugar alcohol that can sometimes cause gastrointestinal distress, and the peanuts are a hard texture that might aggravate TMJ symptoms.",\n  "information_needed": []\n}', 'time': 1791527388}])
# print("saved")

# dataM.delete_chat_history("mary")
# print("deleted")






# docker run -e FERNET_SECRET_KEY="xxxxxxxxxxxxxxxxx" smartbite
# $env:FERNET_SECRET_KEY="xxxxxxxxxxxxxxxxx"; python main.py

