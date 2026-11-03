import hashlib


class MedicalConditions:
    def __init__(self, conditions=[]):
        self._conditions = conditions

    # =========== Attribute Validation ===========
    @staticmethod
    def validate_condition(value): # currently only checks length of name, in real application would cross check with database of all medical condition names.
        if len(value.strip().lower()) <= 1:
            raise ValueError("Please try to enter a recognised name for your medical condition.")
        return value.strip().lower()

    # =========== Edit ===========
    def add_conditions(self, conditions): # takes in a list instead of 1 by 1. For compatibility with GUI.
        validated_conditions = [self.validate_condition(condition) for condition in conditions]
        self._conditions.extend(validated_conditions)

    def remove_conditions(self, condition_indices): # used to be 1 by 1, now it takes in a list of integers. Idea is that the GUI will allow the user to tick the conditions to remove, stored as a list of integers.
        to_remove = set(condition_indices)
        self._conditions = [c for i, c in enumerate(self._conditions) if i not in to_remove]

    # =========== Utility ===========
    def matches_any(self, keywords): # returns True if any keywords are found in list of medical conditions
        return any(keyword.lower() in condition.lower() for condition in self._conditions for keyword in keywords)

    def to_list(self):
        return list(self._conditions)

    def __len__(self):
        return len(self._conditions)


class UserProfile:
    def __init__(self, username, password_hash, age, height, weight, country, ethnicity, gender, medical_conditions=[]):
        self._username = self.validate_username(username)
        self.__password_hash = str(password_hash) # validation not neccessary
        self._age = self.validate_age(age)
        self._height = self.validate_height(height)
        self._weight = self.validate_weight(weight)
        self._country = str(country) # validation during user input
        self._ethnicity = str(ethnicity) # validation during user input
        self._gender = self.validate_gender(gender)
        self.__medical_conditions = MedicalConditions(medical_conditions)

    # =========== Attribute Validation ===========
    @staticmethod
    def validate_username(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Username must be a non-empty string.")
        return value.strip()

    @staticmethod
    def validate_age(value):
        if not isinstance(value, int) or 120 < value < 0:
            raise ValueError("Age must be an integer between 0 and 120.")
        return value

    @staticmethod
    def validate_height(value):
        if not isinstance(value, (int, float)) or 260 < value < 0:
            raise ValueError("Height must be between 0 and 260 cm.")
        return value

    @staticmethod
    def validate_weight(value):
        if not isinstance(value, (int, float)) or 500 < value < 0:
            raise ValueError("Weight must be between 0 and 500 kg.")
        return value

    @staticmethod
    def validate_gender(value):
        if value.strip().lower() not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")
        return value.strip().lower()

    # =========== Password Hashing ===========
    @staticmethod
    def hash_password(plain_password):
        return hashlib.sha256(plain_password.encode()).hexdigest()

    # =========== Profile Create Methods ===========
    @classmethod
    def create(cls, username, password, age, height, weight, country, ethnicity, gender, medical_conditions=[]): # hashes the plain_password and calls the constructor as password is stored as hash, not plain
        return cls(username, cls.hash_password(password), age, height, weight, country, ethnicity, gender, medical_conditions)

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
        return round(self._weight / (self._height ** 2), 2)

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




# Testing
jeff = UserProfile.create(username="jeff", password="Jeff", age=23, height=169.95, weight=74.55, country="Singapore", ethnicity="Chinese", gender="Male", medical_conditions=["high cholesterol", "high blood pressure"])

try:
    jeff.add_medical_conditions(["test", "1", "test2"])
except Exception as e:
    print(e)

print(jeff.medical_conditions)