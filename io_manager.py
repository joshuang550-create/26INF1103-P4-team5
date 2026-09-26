"""The boundary between the user and the application.
"""

green_color = ""

def show_startup_banner():
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

    print("\033[92m" + banner + "\033[0m")


def ask_for_valid_menu_choice(num_options):
    """Ask user for an input and validate their input.

    Args:
        num_options (int): Number of available menu options.

    Returns:
        int: Valid menu choice between 1 and num_options.
    """
    while True:
        user_input = input("\033[92mSmartBite> \033[0m")

        if not user_input.isdigit():
            print("Please select one of the option numbers.")
            continue

        chosen_option = int(user_input)

        if 1 <= chosen_option <= num_options:
            return chosen_option

        print(f"Please select one of the available options between 1 and {num_options}.")


def get_login_menu_choice():
    print("\n═══════════════════════════════════════════════════")
    print(" Welcome to SmartBite!")
    print("═══════════════════════════════════════════════════\n")
    
    print(" \033[92m[1]\033[0m Login")
    print(" \033[92m[2]\033[0m Create Account\n")

    chosen_option = ask_for_valid_menu_choice(2)

    return chosen_option


def get_login_credentials():
    pass


def print_create_user_profile_menu():
    # note that this function will just print the menu and get the user inputs, then call create_user_profile() and pass these inputs as arguments.
    # input from user, save into a dictionary, output the dictionary.
    # the user will not be asked to enter a UID, the function will automatically create one. check against the user_profiles.json to ensure the UID doesnt already exist. (check if this UID is an existing key in the JSON file)
    pass


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
