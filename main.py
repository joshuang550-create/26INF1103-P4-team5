"""Main entry point for the application.
"""

import io_manager
import data_manager
import ai_manager_jeff
import logic_manager


def login_menu():
    while True:
        chosen_option = io_manager.get_login_menu_choice()

        if chosen_option == 1: # Login
            user_profile = data_manager.login_user_profile_from_database(*io_manager.get_login_credentials())
            if user_profile is None:
                io_manager.show_failed_login_message()
                continue # login failed. go to back to login page
            main_menu(user_profile) # login successful. move on to main menu page

        elif chosen_option == 2: # New Profile
            user_profile = io_manager.get_new_profile_info()
            data_manager.save_user_profile_to_database(user_profile)
            io_manager.show_successful_profile_creation_message()
            main_menu(user_profile) # profile creation successful. move on to main menu page

        elif chosen_option == 3: # Close App
            # an app closing message / banner?
            return # ends main function


def main_menu(user_profile):
    while True:
        chosen_option = io_manager.get_main_menu_choice(user_profile)

        if chosen_option == 1: # View Profile
            io_manager.show_user_profile(user_profile)
            continue # back to main menu

        elif chosen_option == 2: # Edit Profile
            if edit_profile_menu(user_profile): # if True, user deleted the profile.
                return # go back to login page

        elif chosen_option == 3: # Check Food




            # put into a loop, maybe as its own function here in main.py


            food_to_check = io_manager.ask_for_check_food_item_name()
            prompt_string = ai_manager_jeff.generate_first_prompt(user_profile)
            response = ai_manager_jeff.send_prompt_to_ai(prompt_string)
            validation_result = ai_manager_jeff.validate_ai_response(response)

            if validation_result != "No Errors":
                response = ai_manager_jeff.send_prompt_to_ai(validation_result) # this should work cause send_prompt_to_ai should auto append the history, which would include the original response with these errors.
                validation_result = ai_manager_jeff.validate_ai_response(response)

            if validation_result != "No Errors":
                # io_manager print some error message saying that something went wrong with the ai's response. Please try again later.
                continue # back to main menu
            
            if response == "Request for more info.":
                more_info_input = io_manager.ask_for_more_information() # is a dict
                more_info_prompt_string = ai_manager_jeff.generate_more_info_prompt(more_info_input) # more_info_input is a python dict {"How much alchohol do you drink a month?":"about 10 cans of beer a month.", "Do u run alot?":"no"}
                response = ai_manager_jeff.send_prompt_to_ai(more_info_prompt_string)

            confidence_score = logic_manager.calculate_response_confidence(ai_response)
            # LOGIC MANAGER FROM HERE ONWARDS...
            generic_prompt_string = logic_manager.generate_generic_response_prompt() # "i am a 20 year olf singaporean chinese. i have diabetes, high blood pressure. what foods do i eat?"


            response = ai_manager_jeff.send_prompt_to_ai(generic_prompt_string) # you should eat banana given your high blood pressure. ...

            io_manager.print_final_output(response)

            continue # back to main menu for now. will call io_manager.show_final_output() later.


















        elif chosen_option == 4: # Log Out
            break # goes back to login page


def edit_profile_menu(user_profile):
    while True:
        chosen_option = io_manager.get_edit_user_profile_choice()

        if chosen_option == 1: # Add Medical Condition
            medical_conditions_input = io_manager.ask_for_medical_conditions(user_profile)
            data_manager.add_profile_medical_condition(user_profile, medical_conditions_input)

        elif chosen_option == 2: # Remove Medical Condition
            medical_conditions_to_remove_input = io_manager.ask_for_medical_conditions_to_remove(user_profile)
            data_manager.remove_profile_medical_condition(user_profile, medical_conditions_to_remove_input)

        elif chosen_option == 3: # Update Age
            user_profile["age"] = io_manager.ask_for_valid_age(standalone=True)

        elif chosen_option == 4: # Update Country of Residence
            user_profile["country"] = io_manager.ask_for_valid_country(standalone=True)

        elif chosen_option == 5: # Update Height
            user_profile["height"] = io_manager.ask_for_valid_height(standalone=True)

        elif chosen_option == 6: # Update Weight
            user_profile["weight"] = io_manager.ask_for_valid_weight(standalone=True)

        elif chosen_option == 7: # Save & Exit
            data_manager.save_user_profile_to_database(user_profile)
            return False # go back to main menu

        elif chosen_option == 8: # Delete Profile
            chosen_option = io_manager.get_delete_user_profile_confirmation()

            if chosen_option in ["y", "yes"]:
                data_manager.delete_user_profile_from_database(user_profile)
                io_manager.show_successful_profile_deletion_message()
                return True # delete profile, go to login page
            
            continue # don't delete, go back to edit profile menu


def main():    
    login_menu()


if __name__ == "__main__":
    main()














# after running prompt_ai(), read the output to see if it is a follow-up request or a final response. 
# if it is a follow-up request, run print_follow_up_request_input() function from io_manager for the 
# user to enter more information that the AI requested.
