"""The boundary between the user and the application.
"""

def print_login_menu():
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


# example for now, make this better
def print_food_item_check_menu():
    pass