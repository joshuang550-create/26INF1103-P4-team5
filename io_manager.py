"""The boundary between the user and the application.
"""

import data_manager

import sys
import getpass # for python 3.14, if docker 3.14 slim is too unstable, may need to change getpass to smth else.

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


def ask_for_valid_gender():
    """Loops until the user enters 'male' or 'female'."""
    while True:
        gender_input = input(" Gender (Male/Female): ").strip().lower()
        if gender_input in ("male", "female"):
            return gender_input
        print(f" {ERROR_COLOR_PREFIX}Gender must be 'Male' or 'Female'.{COLOR_SUFFIX}")


def ask_for_valid_age():
    """Loops until a valid age between 1 and 120 is provided."""
    while True:
        try:
            age_input = int(input(" Age: ").strip())
            if 1 <= age_input <= 120:
                return age_input
            print(f" {ERROR_COLOR_PREFIX}Age must be a positive integer up to 120.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid age number.{COLOR_SUFFIX}")


def ask_for_valid_height():
    """Loops until a valid height between 0.1 and 259.9 is provided."""
    while True:
        try:
            height_input = float(input(" Height (cm): ").strip())
            if 0 < height_input < 260:
                return height_input
            print(f" {ERROR_COLOR_PREFIX}Height must be greater than 0 and less than 260 cm.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid number for height.{COLOR_SUFFIX}")


def ask_for_valid_weight():
    """Loops until a valid weight between 0.1 and 699.9 is provided."""
    while True:
        try:
            weight_input = float(input(" Weight (kg): ").strip())
            if 0 < weight_input < 700:
                return weight_input
            print(f" {ERROR_COLOR_PREFIX}Weight must be greater than 0 and less than 700 kg.{COLOR_SUFFIX}")
        except ValueError:
            print(f" {ERROR_COLOR_PREFIX}Please enter a valid number for weight.{COLOR_SUFFIX}")
            

def ask_for_valid_race():
    """Loops until a valid race found in RACES_CSV is provided."""
    while True:
        race_input = input(" Race: ").strip()
        if data_manager.search_csv_for_string(race_input, RACES_CSV):
            return race_input
        print(f" {ERROR_COLOR_PREFIX}{race_input} is not a valid race.{COLOR_SUFFIX}")
    

def ask_for_valid_country():
    """Loops until a valid country found in COUNTIRES_CSV is provided."""
    while True:
        country_input = input(" Country: ").strip()
        if data_manager.search_csv_for_string(country_input, COUNTRIES_CSV):
            return country_input
        print(f" {ERROR_COLOR_PREFIX}{country_input} is not a valid country.{COLOR_SUFFIX}")


def get_login_menu_choice():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Welcome to SmartBite!")
    print("═══════════════════════════════════════════════════\n")
    
    print(" \033[92m[1]\033[0m Login")
    print(" \033[92m[2]\033[0m New Profile\n")

    chosen_option = ask_for_valid_menu_choice(2)

    return chosen_option


def get_login_credentials():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Login")
    print("═══════════════════════════════════════════════════\n")

    username_input = input(" Username: ")
    password_input = getpass.getpass(" Password: ", echo_char="*")

    return username_input, password_input


def get_new_profile_info():
    clear_terminal()
    show_app_banner()

    print("\n═══════════════════════════════════════════════════")
    print(" Create a new profile")
    print("═══════════════════════════════════════════════════\n")

    while True:
        username_input = input(" Choose a username: ").strip()
        if data_manager.check_taken_username(username_input):
            print(f" {ERROR_COLOR_PREFIX}Username taken, please try another username.{COLOR_SUFFIX}")
            continue
        break

    password_input = getpass.getpass(" Choose a password: ", echo_char="*")
    hashed_password = data_manager.hash_password(password_input)

    gender_input = ask_for_valid_gender()
    age_input = ask_for_valid_age()
    race_input = ask_for_valid_race()
    country_input = ask_for_valid_country()
    height_input = ask_for_valid_height()
    weight_input = ask_for_valid_weight()

    user_profile = {
        "username": username_input,
        "password_hash": hashed_password,
        "gender": gender_input,
        "age": age_input,
        "race": race_input,
        "country": country_input,
        "height": height_input,
        "weight": weight_input
    }

    print(" Your new profile has been created successfully!")

    return user_profile


def print_main_menu():
    pass


def print_user_profile():
    pass


def print_update_user_profile_menu():
    # show an options menu list 1, 2, 3, 4, 5  -- user will enter 1 to add medical condition, 2 to remove medical condition, 3 to change age, 4 to change race, 5 to change country of residence etc.
    # then, ask for the value to add/remove/change to stored as its own variable eg. edit_value.
    # then, call update_user_profile() and pass the chosen option number and the edit_value as an argument to actually update the info. The logic will be in update_user_profile().
    pass


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
