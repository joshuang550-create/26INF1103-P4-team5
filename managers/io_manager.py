"""The boundary between the user and the application.

The GUI hands IOManager raw text from the screen. IOManager turns it into the types the engine
expects, checks it, calls the engine, and hands back results the GUI can show.
"""

from dataclasses import dataclass

from models.errors import InvalidInputError


VERDICT_COLOURS = {"OK": "#3ba776", "CAUTION": "#f2b134", "AVOID": "#E5534B", "UNDETERMINED": "#8a9099"} # same as progress/chart.py
VERDICT_MEANING = {"OK": "Okay to eat", "CAUTION": "Eat with caution", "AVOID": "Best to avoid", "UNDETERMINED": "Could not decide"}


@dataclass(frozen=True)
class FieldCheck: # result of checking one form field
    message: str = "" # hint to show next to the field, "" when the field is fine
    fix: str | None = None # corrected text the user can accept with one click, None when there is no suggestion


@dataclass(frozen=True)
class OutcomeView: # an Outcome turned into what the screen shows
    title: str
    colour: str
    text: str

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

    @staticmethod
    def describe_outcome(outcome): # turns an Outcome into a title, a colour and text lines for the screen
        details = outcome.details()
        if outcome.severity is None: # RecommendationOutcome (fallback)
            lines = [details["message"], "", "You could try instead:"]
            lines += [f"  • {item.get('food', '')}: {item.get('reason', '')}" for item in details.get("recommendations", [])]
        else: # AssessmentOutcome
            lines = [details["reason"]]
            if details["allergens_found"]:
                lines += ["", "Allergens found:"]
                lines += [f"  • {category.replace('_', ' ')}: {', '.join(words)}" for category, words in details["allergens_found"].items()]
            if details["flags"]:
                lines += ["", "Flagged nutrients:"]
                lines += [f"  • {flag['nutrient']}: {flag['value']} ({flag['level']})" for flag in details["flags"]]
            if details["nutrients"]:
                lines += ["", f"Nutrients per {details['portion_g']} g:"]
                lines += [f"  • {nutrient}: {value}" for nutrient, value in details["nutrients"].items()]
            lines += ["", f"AI confidence: {details['confidence']}/10"]
        headline = outcome.headline
        return OutcomeView(f"{headline} – {VERDICT_MEANING.get(headline, '')}", VERDICT_COLOURS.get(headline, "#8a9099"), "\n".join(lines))


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