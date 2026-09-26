"""Main entry point for the application.
"""

import io_manager


def main():
    # after running prompt_ai(), read the output to see if it is a follow-up request or a final response. if it is a follow-up request, run print_follow_up_request_input() function from io_manager for the user to enter more information that the AI requested.
    
    io_manager.show_startup_banner()

    chosen_option = io_manager.get_login_menu_choice()

    if chosen_option == 1: # Login
        #call get_login_credentials
        pass
    elif chosen_option == 2: # Create Account
        pass

if __name__ == "__main__":
    main()




# IDEAS
# log out option? unneccessary but it is a common function to have in an app