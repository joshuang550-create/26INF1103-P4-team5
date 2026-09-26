"""System memory across runs.
"""

import hashlib
import csv
import json
import os
import pathlib


USER_PROFILES = "./user_profiles.json"


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
    """Saves a user profile dictionary into a JSON file as a dict of dicts.

    This function reads existing profiles from the JSON database, appends or
    updates the profile using the username as the master lookup key, and
    saves the file.
    """
    user_profiles = get_all_user_profiles()

    username = str(user_profile["username"])
    user_profiles[username] = user_profile

    with open(USER_PROFILES, "w", encoding="utf-8") as file:
        json.dump(user_profiles, file, indent=4)


def delete_user_profile():
    # if called by print_update_user_profile_menu(), delete the dictionary key-value pair for currently logged in user.
    pass


def add_profile_medical_condition(user_profile, medical_conditions_input):
    user_profile["medical_conditions"].extend(medical_conditions_input)


def remove_profile_medical_condition(user_profile, medical_conditions_to_remove_input):
    user_profile["medical_conditions"] = [
        mc
        for i, mc in enumerate(user_profile["medical_conditions"])
        if i not in medical_conditions_to_remove_input
    ]


def change_profile_age():
    pass


def change_profile_race():
    pass


def change_profile_gender():
    pass


def change_profile_country_of_residence():
    pass


def change_profile_weight():
    # maybe dont need a funtion to calculate BMI since we can just send the weight and height to the prompt as text and let the AI figure it out.
    pass


def change_profile_height():
    pass
