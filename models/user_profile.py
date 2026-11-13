import hashlib
import re

from models.medical_conditions import MedicalConditions
from exceptions.invalid_input_error import InvalidInputError


class UserProfile:
    def __init__(self, username, password_hash, age, height, weight, country, ethnicity, gender, medical_conditions=None):
        self._username = self.validate_username(username)
        self.__password_hash = str(password_hash) # validation not neccessary
        self._age = self.validate_age(age)
        self._height = self.validate_height(height)
        self._weight = self.validate_weight(weight)
        self._country = str(country) # validation during user input
        self._ethnicity = str(ethnicity) # validation during user input
        self._gender = self.validate_gender(gender)
        self.__medical_conditions = MedicalConditions(medical_conditions) # validation during user input

    # =========== Attribute Validation ===========
    @staticmethod
    def validate_username(value):
        if not isinstance(value, str) or not value.strip():
            raise InvalidInputError("Username must be a non-empty string.")
        return value.strip()

    @staticmethod
    def validate_age(value):
        if not isinstance(value, int) or not 0 < value <= 120:
            raise InvalidInputError("Age must be an integer between 0 and 120.")
        return value

    @staticmethod
    def validate_height(value):
        if not isinstance(value, (int, float)) or not 0 < value <= 260:
            raise InvalidInputError("Height must be between 0 and 260 cm.")
        return value

    @staticmethod
    def validate_weight(value):
        if not isinstance(value, (int, float)) or not 0 < value <= 500:
            raise InvalidInputError("Weight must be between 0 and 500 kg.")
        return value

    @staticmethod
    def validate_gender(value):
        if not isinstance(value, str) or value.strip().lower() not in ["male", "female"]:
            raise InvalidInputError("Gender must be 'male' or 'female'")
        return value.strip().lower()

    # =========== Password Hashing ===========
    @staticmethod
    def hash_password(plain_password):
        return hashlib.sha256(plain_password.encode()).hexdigest()

    # =========== Profile Create Methods ===========
    @classmethod
    def create(cls, username, plain_password, age, height, weight, country, ethnicity, gender, medical_conditions=None): # hashes the plain_password and calls the constructor as password is stored as hash, not plain
        return cls(username, cls.hash_password(plain_password), age, height, weight, country, ethnicity, gender, medical_conditions)

    @classmethod
    def from_dict(cls, data): # creates a UserProfile instance from a dictionary, when existing user logs in for example
        return cls(
            username=data.get("username"),
            password_hash=data.get("password_hash"),
            age=data.get("age"),
            height=data.get("height"),
            weight=data.get("weight"),
            country=data.get("country"),
            ethnicity=data.get("ethnicity"),
            gender=data.get("gender"),
            medical_conditions=data.get("medical_conditions", [])
        )

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.__password_hash,
            "age": self._age,
            "height": self._height,
            "weight": self._weight,
            "country": self.country,
            "ethnicity": self.ethnicity,
            "gender": self.gender,
            "medical_conditions": self.__medical_conditions.to_list()
        }

    # =========== Behaviours ===========
    def verify_password(self, plain_password):
        return self.__password_hash == self.hash_password(plain_password)
    
    def add_medical_conditions(self, conditions):
        self.__medical_conditions.add_conditions(conditions)

    def remove_medical_conditions(self, indices):
        self.__medical_conditions.remove_conditions(indices)

    def has_condition_matching(self, keywords):
        return self.__medical_conditions.matches_any(keywords)

    # =========== Read-Only Properties ===========
    @property
    def username(self):
        return self._username

    @property
    def age(self):
        return self._age

    @property
    def height(self):
        return self._height

    @property
    def weight(self):
        return self._weight

    @property
    def country(self):
        return self._country

    @property
    def ethnicity(self):
        return self._ethnicity

    @property
    def gender(self):
        return self._gender

    @property
    def medical_conditions(self):
        return self.__medical_conditions.to_list()

    @property
    def bmi(self):
        return round(self._weight / ((self._height / 100) ** 2), 2)

    @property
    def allergies(self): # used by AllergenDetector
        return [word for word in self.medical_conditions if re.search(r"allergy", word, re.IGNORECASE)] # works because all allergies in conditions.csv ends with the word "Allergy"

    # =========== Profile Edit Setters ===========
    @age.setter
    def age(self, value):
        self._age = self.validate_age(value)

    @height.setter
    def height(self, value):
        self._height = self.validate_height(value)

    @weight.setter
    def weight(self, value):
        self._weight = self.validate_weight(value)

    @country.setter
    def country(self, value):
        self._country = str(value) # validation during user input
