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
                continue # login failed. go to back to login page
            # login successful. move on to main menu page

        elif chosen_option == 2: # New Profile
            user_profile = io_manager.get_new_profile_info()
            data_manager.save_user_profile_to_database(user_profile)
            # profile creation successful. move on to main menu page

        elif chosen_option == 3: # Close App
            # an app closing message / banner?
            return # ends main function

        while True:
            chosen_option = io_manager.get_main_menu_choice(user_profile)

            if chosen_option == 1: # View Profile
                io_manager.show_user_profile(user_profile)
                continue # back to main menu

            elif chosen_option == 2: # Edit Profile
                pass

            elif chosen_option == 3: # Check Food
                pass

            elif chosen_option == 4: # Log Out
                break # goes back to login page











if __name__ == "__main__":
    main()




# IDEAS
# log out option? unneccessary but it is a common function to have in an app