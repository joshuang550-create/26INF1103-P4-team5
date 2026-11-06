from models.user_profile import UserProfile
from models.ai_models import Gemini
from models.openfoodfacts import OpenFoodFactsSearcher
from models.errors import InvalidInputError, LoginFailedError, InvalidActionError

from managers.data_manager import DataManager
from managers.ai_manager import AIManager
from managers.logic_manager import LogicManager, AllergenRule, NutrientThresholdRule, AIConcernRule, AllergenDetector


class AppEngine:
    def __init__(self, data_manager=None, ai_model=None, searcher=None): # optional argument for test suite
        self._data = data_manager or DataManager()
        self._ai = AIManager(self._data, ai_model or Gemini(api_key_supplier=self._data.get_api_key))
        self._logic = LogicManager(rules=[AllergenRule(), NutrientThresholdRule(self._data.get_thresholds()), AIConcernRule()], allergen_detector=AllergenDetector(self._data.get_allergens()))
        self._searcher = searcher or OpenFoodFactsSearcher()
        self._user = None # the logged in UserProfile object instance
        self._reset_check() # always reset for new instance

    # =========== Account ===========
    def register(self, username, plain_password, gender, age, ethnicity, country, height, weight, medical_conditions=None):
        username = UserProfile.validate_username(username) # check if non empty string, raise InvalidInputError
        if self._data.is_username_taken(username):
            raise InvalidInputError("Username taken, please try a different username.")
        if not isinstance(plain_password, str) or not plain_password:
            raise InvalidInputError("Password cannot be empty.")

        profile = UserProfile.create(username, plain_password, age, height, weight, self._valid_country(country), self._valid_ethnicity(ethnicity), gender)
        if medical_conditions:
            profile.add_medical_conditions(medical_conditions)

        self._data.delete_chat_history(username) # ensures new accounts do not have chat history
        self._data.save_profile(profile)
        self._start_session(profile)
        return self.profile
        
    def login(self, username, password):
        profile = self._data.login(username, password)
        if profile is None:
            raise LoginFailedError()
        self._start_session(profile)
        return self.profile
    
    def logout(self):
        self._end_session()

    def delete_account(self):
        profile = self._require_login()
        self._data.delete_chat_history(profile.username)
        self._data.delete_profile(profile)
        self._end_session()

    # =========== Properties ===========
    @property
    def profile(self):
        if self._user is None:
            return None
        return UserProfile.from_dict(self._user.to_dict()) # returns a copy, cant be edited


    # =========== Profile Editing ===========
    def update_age():
        pass

    def update_height():
        pass

    def update_weight():
        pass

    def update_country():
        pass

    def add_medical_conditions():
        pass

    def remove_medical_conditions():
        pass
    
    # =========== Live GUI Input Validation ===========
    def is_username_taken():
        pass

    def is_valid_country():
        pass

    def is_valid_ethnicity():
        pass

    def is_valid_condition():
        pass

    def is_valid_barcode():
        pass

    # =========== Food Check ===========
    def check_food():
        pass

    def answer_questions():
        pass

    def cancel_food_check(): # might not want to implement if adds too much complications to the rest of the code. Idea is to be able to abort
        pass

    # =========== Private Input Validation Helpers ===========
    def _valid_country(self, country):
        if not isinstance(country, str) or not self._data.is_valid_country(country.strip()):
            raise InvalidInputError(f"{country} is not a valid country.")
        return country.strip()

    def _valid_ethnicity(self, ethnicity):
        if not isinstance(ethnicity, str) or not self._data.is_valid_ethnicity(ethnicity.strip()):
            raise InvalidInputError(f"{ethnicity} is not a valid ethnicity.")
        return ethnicity.strip()

    # =========== Private Food Check Helpers ===========
    def _reset_check(self):
        self._check_in_progress = False
        self._attempt = 1 # attempt number for getting an assessment from the AI (eg. low confidence)
        self._rounds = 1 # rounds of questions the AI has asked (follow up)
        self._questions = ()

    # =========== Private Session / Profile Helpers ===========
    def _start_session(self, profile):
        self._user = profile
        self._reset_check()

    def _end_session(self):
        self._user = None
        self._reset_check()

    def _require_login(self):
        if self._user is None:
            raise InvalidActionError("Please log in first.")
        return self._user



