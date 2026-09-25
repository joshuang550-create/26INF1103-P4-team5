"""System memory across runs.
"""

def get_user_profile_from_database():
    # this will read a database "user_profiles.json" file (docker volume) and return the specific key-value pair for the user trying to log in.
    pass


def save_user_profile_to_database():
    # should the user make any changes, this function can overwrite the values in the "user_profiles.json" file for the current logged in user. the key should be a Unique ID.
    pass


def get_user_profile():
    # should return the currently logged in user's profile. The profile should be stored as a dictionary.
    pass


def create_user_profile():
    # this function is not entirely necessary but i will use it just to keep the structure clean. print_create_user_profile_menu() will get the user inputs, then pass them as arguments to this function to then create the profile and save it to the database user_profiles.json
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
