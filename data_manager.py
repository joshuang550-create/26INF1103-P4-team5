"""System memory across runs.
"""

import hashlib
import csv
import json
import os


USER_PROFILES = "./user_profiles.json"


def hash_password(password_input):
    """Converts a plain-text password into a secure SHA-256 hex string."""
    return hashlib.sha256(password_input.encode()).hexdigest()


def search_csv_for_string(search_string, search_csv):
    with open(search_csv, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)

        for row in reader:
            if row and row[0] == search_string:
                return True

        return False


def get_user_profile_from_database():
    # this will read a database "user_profiles.json" file (docker volume) and return the specific key-value pair for the user trying to log in.
    pass


def save_user_profile_to_database(user_profile):
    """Saves a user profile dictionary into a JSON file as a dict of dicts.

    This function reads existing profiles from the JSON database, appends or
    updates the profile using the user's ID as the master lookup key, and
    saves the file.
    """
    master_profiles = {}

    if os.path.exists(USER_PROFILES) and os.path.getsize(USER_PROFILES) > 0: # if false, it will create a new USER_PROFILE JSON file
        try:
            with open(USER_PROFILES, "r", encoding="utf-8") as file:
                master_profiles = json.load(file)
        except json.JSONDecodeError:
            # future implementation to send a notification to admin of this error. admin can then fix it manually. admin will backup the databases every so often as well.
            pass

    profile_id = str(user_profile["id"])
    master_profiles[profile_id] = user_profile

    with open(USER_PROFILES, "w", encoding="utf-8") as file:
        json.dump(master_profiles, file, indent=4)


def get_user_profile():
    # should return the currently logged in user's profile. The profile should be stored as a dictionary.
    pass
    

def delete_user_profile():
    # if called by print_update_user_profile_menu(), delete the dictionary key-value pair for currently logged in user.
    pass


def add_profile_medical_condition():
    pass


def remove_profile_medical_condition():
    pass


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
