"""Shared test helpers: scripted fake AI, fake barcode searcher, temp data folder."""
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from app.app_engine import AppEngine
from managers.data_manager import DataManager
from ai.providers.ai_model import AIModel
from ai.providers.model_response import ModelResponse
from services.openfoodfacts.food_product import FoodProduct
from models.user_profile import UserProfile

NUTRIENT_KEYS = ("sodium_mg", "sugar_g", "saturated_fat_g", "trans_fat_g")


# =========== Sample AI replies ===========
def ai_reply(reason="A plain, simple food.", portion_g=100, concern=False, confidence=90, questions=(), **nutrient_values):
    """Build a JSON string shaped like a valid AI food-check reply.
    nutrient_values (e.g. sodium_mg=700) override the all-zero default nutrients.
    """
    questions = list(questions)
    nutrients = {key: 0 for key in NUTRIENT_KEYS}
    if questions:  # while the AI is asking questions, the app expects placeholders
        return json.dumps({"information_needed": questions, "portion_g": 0, "nutrients": nutrients,
                           "reason": "I need a little more detail.", "potential_concern": False,
                           "confidence_score": 0})
    nutrients.update(nutrient_values)
    return json.dumps({"information_needed": [], "portion_g": portion_g, "nutrients": nutrients,
                       "reason": reason, "potential_concern": concern, "confidence_score": confidence})


def fallback_reply(count=3):
    return json.dumps({"recommendations": [{"food": f"Food {i}", "reason": f"Good for you {i}."} for i in range(count)]})


# =========== Fakes ===========
class FakeModel(AIModel):
    """Returns pre-scripted replies in order and records every prompt it was sent.
    A scripted item that is an Exception is raised instead of returned."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def send(self, prompt, history, system_instruction):
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError("FakeModel ran out of scripted replies: the app called the AI more often than expected.")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        new_history = list(history) + [{"role": "user", "text": prompt, "time": 0}, {"role": "model", "text": reply, "time": 0}]
        return ModelResponse(reply, new_history)


class FakeSearcher:
    def __init__(self, product=None, error=None):
        self.product, self.error, self.calls = product, error, []

    def search(self, barcode):
        self.calls.append(barcode)
        if self.error:
            raise self.error
        return self.product


def sample_product():
    return FoodProduct(barcode="12345678", name="Salty Crackers", brand="CrunchCo", quantity="200 g",
                       ingredients="wheat flour, salt, palm oil", allergens=("gluten",),
                       nutrition_per_100g={"sodium_mg": 800.0, "sugar_g": 2.0, "saturated_fat_g": 3.0, "trans_fat_g": 0.0})


def make_profile(conditions=None, **overrides):
    values = dict(username="tester", plain_password="pw", age=30, height=170.0, weight=65.0,
                  country="Singapore", ethnicity="Chinese", gender="male", medical_conditions=conditions)
    values.update(overrides)
    return UserProfile.create(**values)


# =========== Base test case with a throw-away data folder ===========
class TempDataTestCase(unittest.TestCase):
    """Gives each test its own empty profiles/chats files so tests never touch real data."""
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="smartbite_test_")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.profiles_path = os.path.join(self.tmp, "user_profiles.json")
        self.chats_path = os.path.join(self.tmp, "chats.json")
        patcher = mock.patch.dict(os.environ, {"USER_PROFILES": self.profiles_path, "CHATS": self.chats_path})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.data = DataManager()

    def make_engine(self, replies=(), searcher=None, conditions=None, login=True):
        """Build an AppEngine wired to the fake model and (optionally) register + log in a user."""
        self.model = FakeModel(replies)
        self.searcher = searcher or FakeSearcher()
        engine = AppEngine(data_manager=self.data, ai_model=self.model, searcher=self.searcher)
        if login:
            engine.register("tester", "pw", "male", 30, "Chinese", "Singapore", 170.0, 65.0, conditions)
        return engine
