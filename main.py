"""Main entry point for the application.
"""

import io_manager
import data_manager
import ai_manager
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
            ai_response = check_food_process(user_profile)

            if not ai_response:
                io_manager.show_generic_error_message() # ai_response is empty, no response.
                continue # back to main menu

            logic_response = logic_manager.process_ai_response(ai_response, user_profile)

            if logic_response.get("fallback_prompt"):
                logic_response = ai_manager.send_prompt_to_ai(user_profile, logic_response.get("fallback_prompt")) # returns a dict of food name and detail pairs.

            io_manager.show_final_output(logic_response)
            continue # back to main menu

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


def check_food_process(user_profile):
    food_to_check, food_item_barcode = io_manager.ask_for_check_food_item_name() # user will input a food name and an optional barcode number
    prompt_string = ai_manager.generate_first_prompt(user_profile, food_to_check, food_item_barcode) # returns a full llm prompt as a string

    retry = 2
    while retry > 0:
        response = ai_manager.send_prompt_to_ai(user_profile, prompt_string) # returns the GenerateContentResponse's text attribute

        if not response: # send_prompt_to_ai failed.
            return # go back to main menu
        
        response, validation_result = ai_manager.validate_ai_response(response) # checks if the response has valid structure, content etc. new response here is just json.loads(response.text) - convert str to dict

        if validation_result != "No Errors": # invalid response
            prompt_string = validation_result
            retry -= 1 # retries twice if response is invalid
            continue # prompt again using automated prompt_string generated by validate_ai_response() that tells the ai what is wrong with previous response.

        elif response["status"] == "needs_follow_up":
            more_info_input = io_manager.ask_for_ai_follow_up_input(response) # more_info_input is a dict eg. {"How much alchohol do you drink a month?":"about 10 cans of beer a month.", "Do u run alot?":"no"}
            more_info_prompt_string = ai_manager.generate_more_info_prompt(more_info_input)
            prompt_string = more_info_prompt_string
            continue # prompt again using more info prompt string. send_prompt_to_ai() will automatically append the chat history so original prompt and response will be included.

        else:
            return response #successfully obtained json response from ai

    return # unsuccessful, go back to main menu


def main():    
    login_menu()


if __name__ == "__main__":
    main()
