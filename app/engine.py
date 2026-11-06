from dataclasses import dataclass

from models.user_profile import UserProfile
from models.ai_models import Gemini
from models.openfoodfacts import OpenFoodFactsSearcher
from models.errors import InvalidInputError, LoginFailedError, InvalidActionError, AIResponseError

from managers.data_manager import DataManager
from managers.ai_manager import AIManager
from managers.logic_manager import LogicManager, AllergenRule, NutrientThresholdRule, AIConcernRule, AllergenDetector, ResponseAction


# =========== Helper Type ===========
@dataclass(frozen=True)
class FoodCheckStep: # what the GUI gets back after running check_food and answer_questions
    questions: tuple = () # questions the AI needs answered first. empty when the check is finished
    outcome: object = None # an Outcome object when the check is finished, else None

    @property
    def needs_answers(self):
        return bool(self.questions) # True or False that it needs answers


# =========== App Engine ===========
class AppEngine:
    MAX_QUESTION_ROUNDS = 3 # incase the ai ignores the limit and keeps going, this will force break

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
        return UserProfile.from_dict(self._user.to_dict()) # returns a copy, cant be edited (still an object)


    # =========== Profile Editing ===========
    def update_age(self, age):
        return self._set_field("age", age)

    def update_height(self, height):
        return self._set_field("height", height)

    def update_weight(self, weight):
        return self._set_field("weight", weight)

    def update_country(self, country):
        return self._set_field("country", self._valid_country(country))

    def add_medical_conditions(self, conditions): # list of conditions
        updated = self._copy_of_profile()
        updated.add_medical_conditions(conditions)
        return self._save_updated(updated)

    def remove_medical_conditions(self, indices): # list of positions in profile.medical_conditions starting at 0 (GUI checkbox as input)
        updated = self._copy_of_profile()
        total = len(updated.medical_conditions)
        if not all(isinstance(i, int) and 0 <= i < total for i in indices):
            raise InvalidInputError("Please select one of the listed medical conditions.")
        updated.remove_medical_conditions(indices)
        return self._save_updated(updated)
    
    # =========== Live GUI Input Validation ===========
    def is_username_taken(self, username):
        return self._data.is_username_taken(username.strip())

    def is_valid_country(self, country):
        return self._data.is_valid_country(country.strip())

    def is_valid_ethnicity(self, ethnicity):
        return self._data.is_valid_ethnicity(ethnicity.strip())

    def is_valid_condition(self, condition):
        return self._data.is_valid_condition(condition.strip()) # returns True/False. use to check if it is in the csv, if it is not, run rapidfuzz

    @staticmethod
    def is_valid_barcode(barcode):
        return OpenFoodFactsSearcher.is_valid_barcode(barcode)

    # =========== Food Check ===========
    def check_food(self, food_name, barcode=""): # starts a new food check
        profile = self._require_login()
        food_name = self._valid_food_name(food_name)
        product = self._find_product(barcode) # run before AI call so bad barcode doesnt matter

        self._reset_check()
        return self._next_step(self._ai.check_food(profile, food_name, product))

    def answer_questions(self, answers): # answers = {question: answer}, one for every question in the last step
        profile = self._require_login()
        if not self._check_in_progress:
            raise InvalidActionError("There is no food check waiting for answers.")
        answers = self._valid_answers(answers)

        return self._next_step(self._ai.follow_up(profile, answers))

    def cancel_food_check(self):
        self._reset_check()

    # =========== Private Input Validation Helpers ===========
    def _valid_country(self, country):
        if not isinstance(country, str) or not self._data.is_valid_country(country.strip()):
            raise InvalidInputError(f"{country} is not a valid country.")
        return country.strip()

    def _valid_ethnicity(self, ethnicity):
        if not isinstance(ethnicity, str) or not self._data.is_valid_ethnicity(ethnicity.strip()):
            raise InvalidInputError(f"{ethnicity} is not a valid ethnicity.")
        return ethnicity.strip()

    def _valid_food_name(self, food_name):
        if not isinstance(food_name, str) or len(food_name.strip()) <= 1:
            raise InvalidInputError("Please try to enter a recognised name for the food item.")
        return food_name.strip()

    def _find_product(self, barcode): # FoodProduct or None if no barcode was given or openfoodfacts doesnt know it
        barcode = (barcode or "").strip()
        if not barcode:
            return None
        if not self.is_valid_barcode(barcode):
            raise InvalidInputError("A barcode must be 8, 12 or 13 digits, or left blank.")
        return self._searcher.search(barcode) # raises FoodLookupError if openfoodfacts cannot be reached

    def _valid_answers(self, answers):
        if not isinstance(answers, dict):
            raise InvalidInputError("Please answer every question.")
        cleaned = {}
        for question in self._questions:
            answer = answers.get(question)
            if not isinstance(answer, str) or not answer.strip():
                raise InvalidInputError("Please answer every question.")
            cleaned[question] = answer.strip()
        return cleaned

    # =========== Private Food Check Helpers ===========
    def _reset_check(self):
        self._check_in_progress = False
        self._attempt = 1 # attempt number for getting an assessment from the AI (eg. low confidence)
        self._rounds = 1 # rounds of questions the AI has asked (follow up)
        self._questions = ()

    def _next_step(self, assessment): # decides what the next step is after each AI response. followup, reprompt, fallback
        while True:
            if assessment.needs_follow_up:
                self._rounds += 1
                if self._rounds > self.MAX_QUESTION_ROUNDS:
                    self._reset_check()
                    raise AIResponseError("The AI asked too many follow-up questions. Please try again with more details about the food.")
                self._check_in_progress = True
                self._questions = tuple(assessment.information_needed)
                return FoodCheckStep(questions=self._questions)

            evaluation = self._logic.evaluate(assessment, self._user, self._attempt)

            if evaluation.action in (ResponseAction.ACCEPT, ResponseAction.AVOID):
                outcome = self._logic.build_outcome(evaluation)
            elif evaluation.action is ResponseAction.REPROMPT: # not confident enough, ask the AI to look again
                self._attempt += 1
                assessment = self._ai.reprompt(self._user)
                continue
            else: # ResponseAction.FALLBACK: still not confident after the reprompt
                outcome = self._logic.build_fallback_outcome(self._ai.fallback(self._user))

            self._reset_check()
            return FoodCheckStep(outcome=outcome)

    # =========== Private Session Helpers ===========
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

    # =========== Private Profile Helpers ===========
    def _copy_of_profile(self):
        return UserProfile.from_dict(self._require_login().to_dict())

    def _save_updated(self, updated):
        self._data.save_profile(updated) # may raise DataError
        self._user = updated # only replaced after saving worked
        return self.profile

    def _set_field(self, field, value): # works on a copy the real profile is untouched
        updated = self._copy_of_profile()
        setattr(updated, field, value)
        return self._save_updated(updated)
