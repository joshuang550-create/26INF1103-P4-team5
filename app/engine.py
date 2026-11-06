from models.user_profile import UserProfile
from models.ai_models import Gemini
from models.openfoodfacts import OpenFoodFactsSearcher
from models.errors import InvalidInputError, LoginFailedError

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

    # =========== Account ===========
    def register():
        pass

    def login():
        pass

    def logout():
        pass

    def delete_account():
        pass

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
