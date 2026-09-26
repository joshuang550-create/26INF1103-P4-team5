"""Main entry point for the application.
"""

import io_manager
import data_manager


def main():
    # after running prompt_ai(), read the output to see if it is a follow-up request or a final response. if it is a follow-up request, run print_follow_up_request_input() function from io_manager for the user to enter more information that the AI requested.
    while True:
        chosen_option = io_manager.get_login_menu_choice()

        if chosen_option == 1: # Login
            user_profile = data_manager.login_user_profile_from_database(*io_manager.get_login_credentials())
            if user_profile == None:
                continue # login failed
            break # login successful

        elif chosen_option == 2: # New Profile
            data_manager.save_user_profile_to_database(io_manager.get_new_profile_info())
            break # profile creation successful


    print("Placeholder for main menu after login")
    io_manager.print_main_menu()













if __name__ == "__main__":
    main()




# IDEAS
# log out option? unneccessary but it is a common function to have in an app