"""The boundary between the user and the application.

The GUI hands IOManager raw text from the screen. IOManager turns it into the types the engine
expects, checks it, calls the engine, and hands back results the GUI can show.
"""

from dataclasses import dataclass

from models.errors import InvalidInputError


@dataclass(frozen=True)
class FieldCheck: # result of checking one form field
    message: str = "" # hint to show next to the field, "" when the field is fine
    fix: str | None = None # corrected text the user can accept with one click, None when there is no suggestion


class IOManager:
    def __init__(self, engine):
        self._engine = engine

    # =========== Account ===========
    @property
    def profile(self):
        return self._engine.profile

    def login(self, username, password):
        return self._engine.login(username.strip(), password)

    def register(self, form): # form = {field: text} straight from the register screen
        conditions = self.split_conditions(form.get("conditions", ""))
        return self._engine.register(
            username=form.get("username", ""),
            plain_password=form.get("password", ""),
            gender=form.get("gender", ""),
            age=self.to_number(form.get("age", ""), "Age", int),
            ethnicity=form.get("ethnicity", ""),
            country=form.get("country", ""),
            height=self.to_number(form.get("height", ""), "Height", float),
            weight=self.to_number(form.get("weight", ""), "Weight", float),
            medical_conditions=conditions or None,
        )

    def logout(self):
        self._engine.logout()

    # =========== Live Field Checks ===========
    def check_field(self, key, text):
        value = text.strip()
        engine = self._engine
        if key == "username" and value and engine.is_username_taken(value):
            return FieldCheck("Username taken")
        if key == "country" and value and not engine.is_valid_country(value):
            return FieldCheck("Not a recognised country")
        if key == "ethnicity" and value and not engine.is_valid_ethnicity(value):
            return FieldCheck("Not a recognised ethnicity")
        if key == "conditions":
            unknown = [c for c in self.split_conditions(value) if not engine.is_valid_condition(c)]
            if unknown:
                return FieldCheck(f"Not recognised: {', '.join(unknown)}")
        return FieldCheck()

    # =========== Food Check ===========
    def check_food(self, food_name, barcode=""):
        return self._engine.check_food(food_name, barcode)

    def answer_questions(self, answers):
        return self._engine.answer_questions(answers)

    def cancel_food_check(self):
        self._engine.cancel_food_check()

    # =========== Converting Text ===========
    @staticmethod
    def to_number(text, label, kind): # "25" -> 25. kind is int or float
        try:
            return kind(str(text).strip())
        except ValueError:
            raise InvalidInputError(f"{label} must be a number.") from None

    @staticmethod
    def split_conditions(text): # "Asthma, Diabetes" -> ["Asthma", "Diabetes"]
        return [part.strip() for part in text.split(",") if part.strip()]