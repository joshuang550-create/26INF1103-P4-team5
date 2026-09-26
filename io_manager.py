"""The boundary between the user and the application.
"""

import sys

import getpass # for python 3.14, if docker 3.14 slim is too unstable, may need to change getpass to smth else.

import data_manager

COLOR_SUFFIX = "\033[0m"
ERROR_COLOR_PREFIX = "\033[91m"
APP_COLOR_PREFIX = "\033[92m"
COUNTRIES_CSV = "./countries.csv"
RACES_CSV = "./races.csv"


def clear_terminal():
    """Clears the terminal screen using ANSI escape code."""
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()


def show_app_banner():
    """Prints the SmartBite ASCII art banner to the terminal.

    This function prints a stylized, multi-line ASCII art title banner 
    colored green using ANSI escape codes.
    """
    banner = r"""
   _____                      _   ____  _ _       
  / ____|                    | | |  _ \(_) |      
 | (___  _ __ ___   __ _ _ __| |_| |_) |_| |_ ___ 
  \___ \| '_ ` _ \ / _` | '__| __|  _ <| | __/ _ \
  ____) | | | | | | (_| | |  | |_| |_) | | ||  __/
 |_____/|_| |_| |_|\__,_|_|   \__|____/|_|\__\___|
    """

    print(APP_COLOR_PREFIX + banner + COLOR_SUFFIX)


def ask_for_valid_menu_choice(num_options):
    """Ask user for an input and validate their input.

    Args:
        num_options (int): Number of available menu options.

    Returns:
        int: Valid menu choice between 1 and num_options.
    """
    while True:
        user_input = input(f"{APP_COLOR_PREFIX}SmartBite> {COLOR_SUFFIX}")

        if not user_input.isdigit():
            print(f" {ERROR_COLOR_PREFIX}Please select one of the option numbers.{COLOR_SUFFIX}")
            continue

        chosen_option = int(user_input)

        if 1 <= chosen_option <= num_options:
            return chosen_option

        print(f" {ERROR_COLOR_PREFIX}Please select one of the available options between 1 and {num_options}.{COLOR_SUFFIX}")


def ask_for_valid_username():
    """Loops until the user enters a username that has not already been taken."""
    while True:
        username_input = input(f" {APP_COLOR_PREFIX}Choose a username:{COLOR_SUFFIX} ").strip()
        if data_manager.check_taken_username(username_input):
            print(f" {ERROR_COLOR_PREFIX}Username taken, please try another username.{COLOR_SUFFIX}")
            continue
        return username_input
    

def ask_for_valid_gender():
    """Loops until the user enters 'male' or 'female'."""
    while True:
        gender_input = input(f" {APP_COLOR_PREFIX}Gender (Male/Female):{COLOR_SUFFIX} ").strip().lower()
        if gender_input in ("male", "female"):
            return gender_input
        print(f" {ERROR_COLOR_PREFIX}Gender must be 'Male' or 'Female'.{COLOR_SUFFIX}")


def ask_for_valid_age(standalone=False):
    """Loops until a valid age between 1 and 120 is provided.

    standalone set to True will show a full UI page.
    """
    if standalone == True:
        clear_terminal()
        show_app_banner()

        print("\n═══════════════════════════════════════════════════")
        print(" Enter your new age.")
        print("═══════════════════════════════════════════════════\n")

    while True:
        try:
            age_input = int(input(f" {APP_COLOR_PREFIX}Age:{COLOR_SUFFIX} ").strip())
            if 1 <= age_input <= 120:
                return age_input
            print(f" {ERROR_COLOR_PREFIX}Age must be a positive integer up to 120.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid age number.{COLOR_SUFFIX}")


def ask_for_valid_height(standalone=False):
    """Loops until a valid height between 0.1 and 259.9 is provided.
    
    standalone set to True will show a full UI page.
    """
    if standalone == True:
        clear_terminal()
        show_app_banner()

        print("\n═══════════════════════════════════════════════════")
        print(" Enter your new height.")
        print("═══════════════════════════════════════════════════\n")

    while True:
        try:
            height_input = float(input(f" {APP_COLOR_PREFIX}Height (cm):{COLOR_SUFFIX} ").strip())
            if 0 < height_input < 260:
                return height_input
            print(f" {ERROR_COLOR_PREFIX}Height must be greater than 0 and less than 260 cm.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid number for height.{COLOR_SUFFIX}")


def ask_for_valid_weight(standalone=False):
    """Loops until a valid weight between 0.1 and 699.9 is provided.
    
    standalone set to True will show a full UI page.
    """
    if standalone == True:
        clear_terminal()
        show_app_banner()

        print("\n═══════════════════════════════════════════════════")
        print(" Enter your new weight.")
        print("═══════════════════════════════════════════════════\n")

    while True:
        try:
            weight_input = float(input(f" {APP_COLOR_PREFIX}Weight (kg):{COLOR_SUFFIX} ").strip())
            if 0 < weight_input < 700:
                return weight_input
            print(f" {ERROR_COLOR_PREFIX}Weight must be greater than 0 and less than 700 kg.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid number for weight.{COLOR_SUFFIX}")
            

def ask_for_valid_race():
    """Loops until a valid race found in RACES_CSV is provided."""
    while True:
        race_input = input(f" {APP_COLOR_PREFIX}Race:{COLOR_SUFFIX} ").strip()
        if data_manager.search_csv_for_string(race_input, RACES_CSV):
            return race_input
        print(f" {ERROR_COLOR_PREFIX}{race_input} is not a valid race.{COLOR_SUFFIX}")
    

def ask_for_valid_country(standalone=False):
    """Loops until a valid country found in COUNTIRES_CSV is provided.
        
    standalone set to True will show a full UI page.
    """
    if standalone == True:
        clear_terminal()
        show_app_banner()

        print("\n═══════════════════════════════════════════════════")
        print(" Enter your new country of residence.")
        print("═══════════════════════════════════════════════════\n")
        
    while True:
        country_input = input(f" {APP_COLOR_PREFIX}Country:{COLOR_SUFFIX} ").strip()
        if data_manager.search_csv_for_string(country_input, COUNTRIES_CSV):
            return country_input
        print(f" {ERROR_COLOR_PREFIX}{country_input} is not a valid country.{COLOR_SUFFIX}")


def show_list_of_medical_conditions(user_profile):
    for i, mc in enumerate(user_profile.get("medical_conditions", ""), start=1):
        print(f" {APP_COLOR_PREFIX}Medical Condition {i}:{COLOR_SUFFIX} {mc}")


def ask_for_medical_conditions(user_profile):
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Enter your new medical conditions.")
    print("═══════════════════════════════════════════════════\n") 
    show_list_of_medical_conditions(user_profile)

    medical_conditions = []
    i = len(user_profile.get("medical_conditions", "")) + 1

    print(f"\n {APP_COLOR_PREFIX}<Once you are done, enter 'done'>{COLOR_SUFFIX}")

    while True:
        medical_condition_input = input(f" {APP_COLOR_PREFIX}Medical Condition {i}:{COLOR_SUFFIX} ").strip().lower()

        if medical_condition_input == "done":
            return medical_conditions

        if len(medical_condition_input) > 1:
            medical_conditions.append(medical_condition_input)
            i += 1
        else:
            print(f" {ERROR_COLOR_PREFIX}Please try to enter a recognised name for your medical condition.{COLOR_SUFFIX}")


def ask_for_medical_conditions_to_remove(user_profile):
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Enter the medical condition number to remove it.")
    print("═══════════════════════════════════════════════════\n") 
    show_list_of_medical_conditions(user_profile)

    print(f"\n {APP_COLOR_PREFIX}<Once you are done, enter 'done'>{COLOR_SUFFIX}")

    medical_conditions_to_remove = []
    number_of_existing_conditions = len(user_profile.get("medical_conditions", ""))

    while True:
        medical_condition_input = input(f" {APP_COLOR_PREFIX}Medical Condition Number:{COLOR_SUFFIX} ").strip().lower()

        if medical_condition_input == "done":
            return medical_conditions_to_remove

        if not medical_condition_input.isdigit():
            print(f" {ERROR_COLOR_PREFIX}Please select one of the medical condition numbers.{COLOR_SUFFIX}")
            continue

        chosen_option = int(medical_condition_input)

        if 1 <= chosen_option <= number_of_existing_conditions:
            medical_conditions_to_remove.append(chosen_option-1) 
        else:
            print(f" {ERROR_COLOR_PREFIX}Please select one of the available options between 1 and {number_of_existing_conditions}.{COLOR_SUFFIX}")


def get_login_menu_choice():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Welcome to SmartBite!")
    print("═══════════════════════════════════════════════════\n")
    
    print(f" {APP_COLOR_PREFIX}[1]{COLOR_SUFFIX} Login")
    print(f" {APP_COLOR_PREFIX}[2]{COLOR_SUFFIX} New Profile")
    print(f" {APP_COLOR_PREFIX}[3]{COLOR_SUFFIX} Close\n")

    chosen_option = ask_for_valid_menu_choice(3)

    return chosen_option


def get_login_credentials():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Login")
    print("═══════════════════════════════════════════════════\n")

    username_input = input(f" {APP_COLOR_PREFIX}Username:{COLOR_SUFFIX} ")
    password_input = getpass.getpass(f" {APP_COLOR_PREFIX}Password:{COLOR_SUFFIX} ", echo_char="*")

    return username_input, password_input


def get_new_profile_info():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Create a new profile")
    print("═══════════════════════════════════════════════════\n")


    username_input = ask_for_valid_username()

    password_input = getpass.getpass(f" {APP_COLOR_PREFIX}Choose a password:{COLOR_SUFFIX}  ", echo_char="*")
    hashed_password_input = data_manager.hash_password(password_input)

    gender_input = ask_for_valid_gender()
    age_input = ask_for_valid_age()
    race_input = ask_for_valid_race()
    country_input = ask_for_valid_country()
    height_input = ask_for_valid_height()
    weight_input = ask_for_valid_weight()

    medical_conditions_input = ask_for_medical_conditions()

    user_profile = {
        "username": username_input,
        "password_hash": hashed_password_input,
        "gender": gender_input,
        "age": age_input,
        "race": race_input,
        "country": country_input,
        "height": height_input,
        "weight": weight_input,
        "medical_conditions": medical_conditions_input
    }

    print(" Your new profile has been created successfully!")

    return user_profile


def get_main_menu_choice(user_profile):
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(f" What would you like to do today, {user_profile.get("username", "")}")
    print("═══════════════════════════════════════════════════\n")

    print(f" {APP_COLOR_PREFIX}[1]{COLOR_SUFFIX} View Profile")
    print(f" {APP_COLOR_PREFIX}[2]{COLOR_SUFFIX} Edit Profile")
    print(f" {APP_COLOR_PREFIX}[3]{COLOR_SUFFIX} Check Food")
    print(f" {APP_COLOR_PREFIX}[4]{COLOR_SUFFIX} Log Out\n")

    chosen_option = ask_for_valid_menu_choice(4)

    return chosen_option


def show_user_profile(user_profile):
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(f" Here is your profile, {user_profile.get("username", "")}")
    print("═══════════════════════════════════════════════════\n")

    print(f" {APP_COLOR_PREFIX}Username:{COLOR_SUFFIX} {user_profile.get("username", "")}")
    print(f" {APP_COLOR_PREFIX}Gender:{COLOR_SUFFIX} {user_profile.get("gender", "")}")
    print(f" {APP_COLOR_PREFIX}Age:{COLOR_SUFFIX} {user_profile.get("age", "")}")
    print(f" {APP_COLOR_PREFIX}Race:{COLOR_SUFFIX} {user_profile.get("race", "")}")
    print(f" {APP_COLOR_PREFIX}Country of Residence:{COLOR_SUFFIX} {user_profile.get("country", "")}")
    print(f" {APP_COLOR_PREFIX}Height:{COLOR_SUFFIX} {user_profile.get("height", "")}cm")
    print(f" {APP_COLOR_PREFIX}Weight:{COLOR_SUFFIX} {user_profile.get("weight", "")}kg\n")

    show_list_of_medical_conditions(user_profile)

    input(f"\n {APP_COLOR_PREFIX}<Press enter to exit>{COLOR_SUFFIX} ")


def get_edit_user_profile_choice():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" What would you like to edit?")
    print("═══════════════════════════════════════════════════\n")

    print(f" {APP_COLOR_PREFIX}[1]{COLOR_SUFFIX} Add Medical Condition")
    print(f" {APP_COLOR_PREFIX}[2]{COLOR_SUFFIX} Remove Medical Condition")

    print(f" {APP_COLOR_PREFIX}[3]{COLOR_SUFFIX} Update Age")
    print(f" {APP_COLOR_PREFIX}[4]{COLOR_SUFFIX} Update Country of Residence")
    print(f" {APP_COLOR_PREFIX}[5]{COLOR_SUFFIX} Update Height")
    print(f" {APP_COLOR_PREFIX}[6]{COLOR_SUFFIX} Update Weight")

    print(f" {APP_COLOR_PREFIX}[7]{COLOR_SUFFIX} Save & Exit\n")

    print(f" {ERROR_COLOR_PREFIX}[8] Delete Profile{COLOR_SUFFIX}\n")

    chosen_option = ask_for_valid_menu_choice(8)

    return chosen_option


def get_delete_user_profile_confirmation():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Are you sure you want to delete this profile?")
    print("═══════════════════════════════════════════════════\n")

    print(f"\n                      {ERROR_COLOR_PREFIX}<y/n>{COLOR_SUFFIX} ")

    while True:
        confirm = input(f"{APP_COLOR_PREFIX}SmartBite> {COLOR_SUFFIX}")

        if confirm in ['yes', 'y', 'no', 'n']:
            return confirm

        print(f" {ERROR_COLOR_PREFIX}Please enter either 'yes' or 'no'.")


def print_check_food_item_input():
    # this is a big thing on its own, this is just a placeholder function for now.
    pass


def print_follow_up_request_input():
    # for the user to enter more information that the AI requested.
    # the format for this should
    pass


def print_final_output():
    # more to this. Just a temporary placeholder to note that there will be functions to print out the final output response for the user to see after all the ai and logic managers do their processing.
    pass

