"""System memory across runs.
"""

import os
import csv
import hashlib
import json
import pathlib

from cryptography.fernet import Fernet

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

USER_PROFILES = os.getenv("USER_PROFILES", str(BASE_DIR / "data" / "user_profiles.json"))
CHAT_HISTORY = os.getenv("CHATS", str(BASE_DIR / "data" / "./chats.json"))
ALLERGENS_FILE = os.getenv("ALLERGENS", str(BASE_DIR / "lookup" / "./allergens.json")) 
THRESHOLDS_FILE = os.getenv("THRESHOLDS", str(BASE_DIR / "lookup" / "./thresholds.json"))

ENCRYPTED_API_KEY = os.getenv("ENCRYPTED_API_KEY", str(BASE_DIR / "./encrypted_api_key.bin"))


# io_manager

def get_all_user_profiles():
    """Load data from user_profiles JSON file and return it as a dictionary.

    If the specified file does not exist, a new file is created.

    If the file exists but cannot be read or contains invalid JSON,
    the function attempts to use a new filename by adding an
    incrementing number to the original filename.

    For example:
        user_profiles.json
        user_profiles1.json
        user_profiles2.json
        user_profiles3.json

    Args:
        filename (str): Name or path of the JSON file.

    Returns:
        dict: The data stored in the JSON file. Returns an empty
            dictionary if a new file is created.
    """
    original_path = pathlib.Path(USER_PROFILES)
    counter = 0

    while True:
        if counter == 0:
            current_path = original_path
        else:
            current_path = (
                original_path.parent
                / f"{original_path.stem}{counter}{original_path.suffix}"
            )

        # Try to read the file if it already exists.
        if current_path.exists():
            try:
                with current_path.open("r", encoding="utf-8") as file:
                    data = json.load(file)

                if not isinstance(data, dict):
                    raise ValueError(
                        "JSON file does not contain a dictionary."
                    )

                return data

            except (
                OSError,
                json.JSONDecodeError,
                UnicodeDecodeError,
                ValueError,
            ):
                counter += 1
                continue

        # File does not exist, so create it.
        try:
            with current_path.open("w", encoding="utf-8") as file:
                json.dump({}, file, indent=4)

            return {}

        except OSError:
            counter += 1


def hash_password(password_input):
    """Converts a plain-text password into a secure SHA-256 hex string."""
    return hashlib.sha256(password_input.encode()).hexdigest()


def search_csv_for_string(search_string, search_csv):
    """Searches for a string within a CSV file."""
    with open(search_csv, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            if row and row[0].lower() == search_string.lower():
                return True

        return False


def check_taken_username(username_input):
    user_profiles = get_all_user_profiles()

    for user_profile in user_profiles.values():
        if user_profile.get("username", "").strip().lower() == username_input.strip().lower():
            return True # username taken already
        
    return False # username not taken yet


def login_user_profile_from_database(username_input, password_input):
    user_profiles = get_all_user_profiles()

    hashed_password_input = hash_password(password_input)

    for user_profile in user_profiles.values():
        stored_username = user_profile.get("username", "").strip().lower()
        stored_hashed_password = user_profile.get("password_hash", "")

        if stored_username == username_input.strip().lower():
            if stored_hashed_password == hashed_password_input:
                return user_profile # successful login

    return None # failed login

    
def save_user_profile_to_database(user_profile):
    """Saves a user profile dictionary into the JSON file as a dict of dicts.

    This function reads existing profiles from the JSON database, appends or
    updates the profile using the username as the master lookup key, and
    saves the file.
    """
    user_profiles = get_all_user_profiles()

    username = str(user_profile["username"])
    user_profiles[username] = user_profile

    with open(USER_PROFILES, "w", encoding="utf-8") as file:
        json.dump(user_profiles, file, indent=4)


def delete_user_profile_from_database(user_profile):
    """Deletes a user profile dictionary from the JSON file.

    This function reads existing profiles from the JSON database, deletes 
    the target profile using the username as the master lookup key, and
    saves the file.
    """
    user_profiles = get_all_user_profiles()

    username = str(user_profile["username"])
    del user_profiles[username]

    with open(USER_PROFILES, "w", encoding="utf-8") as file:
        json.dump(user_profiles, file, indent=4)
    

def add_profile_medical_condition(user_profile, medical_conditions_input):
    user_profile["medical_conditions"].extend(medical_conditions_input)


def remove_profile_medical_condition(user_profile, medical_conditions_to_remove_input):
    user_profile["medical_conditions"] = [
        mc
        for i, mc in enumerate(user_profile["medical_conditions"])
        if i not in medical_conditions_to_remove_input
    ]


# ai_manager

def load_chat_history():
    if not os.path.exists(CHAT_HISTORY):
        return {}
    with open(CHAT_HISTORY, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chats(history):
    with open(CHAT_HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def get_ai_api_key():
    secret_key = os.getenv("FERNET_SECRET_KEY")

    with open(ENCRYPTED_API_KEY, "rb") as f:
        encrypted_key = f.read()

    return Fernet(secret_key).decrypt(encrypted_key).decode()

    # docker run -e FERNET_SECRET_KEY="xxxxxxxxxxxxxxxxx" smartbite
    # $env:FERNET_SECRET_KEY="xxxxxxxxxxxxxxxxx"; python main.py


# logic_manager

def load_thresholds(path=THRESHOLDS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["nutrients"]


def load_allergens(path=ALLERGENS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["allergen_synonyms"]
