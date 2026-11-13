"""The boundary between the user and the application.

The GUI hands IOManager raw text from the screen. IOManager turns it into the types the engine
expects, checks it, calls the engine, and hands back results the GUI can show.
"""

import csv
import os
import pathlib
from dataclasses import dataclass

from rapidfuzz import fuzz, process, utils
from models.errors import InvalidInputError


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

LOOKUP_FILES = { # same files and environment variables as DataManager
    "country": os.getenv("COUNTRIES", str(BASE_DIR / "lookup" / "countries.csv")),
    "ethnicity": os.getenv("ETHNICITIES", str(BASE_DIR / "lookup" / "ethnicities.csv")),
    "conditions": os.getenv("CONDITIONS", str(BASE_DIR / "lookup" / "conditions.csv")),
}
MATCH_CUTOFF = 80 # rapidfuzz score out of 100. Below this, the guess is too far off to suggest


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
    def __init__(self, engine, lookups=None): # lookups is optional, for the test suite
        self._engine = engine
        self._lookups = lookups or {kind: self._read_lookup(path) for kind, path in LOOKUP_FILES.items()}

    # =========== Account ===========
    @property
    def profile(self):
        return self._engine.profile

    def login(self, username, password):
        return self._engine.login(username.strip(), password)

    def register(self, form): # form = {field: text} straight from the register screen
        conditions = self.split_conditions(form.get("conditions", ""))
        self._require_known_conditions(conditions)
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
        if key == "username" and value and self._engine.is_username_taken(value):
            return FieldCheck("Username taken")
        if key in ("country", "ethnicity") and value and not self._is_known(key, value):
            suggestion = self.suggest(key, value)
            if suggestion:
                return FieldCheck(f"Did you mean {suggestion}?", fix=suggestion)
            return FieldCheck(f"Not a recognised {key}")
        if key == "conditions":
            return self._check_conditions(self.split_conditions(value))
        return FieldCheck()

    def suggest(self, kind, text): # closest entry in the lookup list, or None if nothing is close enough
        match = process.extractOne(text, self._lookups[kind], scorer=fuzz.ratio, processor=utils.default_process, score_cutoff=MATCH_CUTOFF)
        return match[0] if match else None

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

    # =========== Progress ===========
    def trend_chart(self):
        return self._engine.trend_chart()

    def weekly_chart(self):
        return self._engine.weekly_chart()

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


    # =========== Private Helpers ===========
    @staticmethod
    def _read_lookup(path):
        try:
            with open(path, newline="", encoding="utf-8") as file:
                return [row[0].strip() for row in csv.reader(file) if row and row[0].strip()]
        except OSError:
            return [] # no list means no suggestions. The engine still does the real check

    def _is_known(self, kind, value):
        return value.lower() in (item.lower() for item in self._lookups[kind])

    def _check_conditions(self, conditions):
        unknown = [c for c in conditions if not self._is_known("conditions", c)]
        if not unknown:
            return FieldCheck()
        fixes = {c: self.suggest("conditions", c) for c in unknown}
        if all(fixes.values()):
            return FieldCheck(f"Did you mean {', '.join(fixes.values())}?", fix=", ".join(fixes.get(c, c) for c in conditions))
        return FieldCheck(f"Not recognised: {', '.join(unknown)}")

    def _require_known_conditions(self, conditions): # the engine saves conditions as typed, so unknown ones are stopped here
        problem = self._check_conditions(conditions)
        if problem.message:
            raise InvalidInputError(problem.message)