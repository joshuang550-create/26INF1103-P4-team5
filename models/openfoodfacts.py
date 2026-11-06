from dataclasses import dataclass, field

import openfoodfacts


# =========== Error ===========
class FoodLookupError(Exception):
    """Open Food Facts could not be reached or returned data we cannot read."""


# =========== Helper Type ===========
@dataclass(frozen=True)
class FoodProduct:
    barcode: str
    name: str
    brand: str
    quantity: str
    ingredients: str
    allergens: tuple = () # ("shrimp", "peanut")
    nutrition_per_100g: dict = field(default_factory=dict)


# =========== Open Food Facts Searcher ===========
class OpenFoodFactsSearcher:
    VALID_LENGTHS = (8, 12, 13) # EAN-8, UPC-A, EAN-13
    FIELDS = ["code", "product_name", "brands", "quantity", "ingredients_text", "allergens_tags", "nutriments"]
    NUTRIENTS = {
        "sodium_mg": ("sodium_100g", 1000),
        "sugar_g": ("sugars_100g", 1),
        "saturated_fat_g": ("saturated-fat_100g", 1),
        "trans_fat_g": ("trans-fat_100g", 1),
    }

    def __init__(self, user_agent="SmartBite/2.0", timeout=10, api=None):
        self._user_agent = user_agent # Open Food Facts asks apps to identify themselves
        self._timeout = timeout # seconds
        self._api = api # None = build the real client on first use

    # =========== Public Methods ===========
    @classmethod
    def is_valid_barcode(cls, barcode): # for live input validation in GUI
        code = str(barcode).strip()
        return code.isascii() and code.isdigit() and len(code) in cls.VALID_LENGTHS

    def search(self, barcode):
        code = str(barcode).strip()
        if not self.is_valid_barcode(code):
            raise ValueError("A barcode must be 8, 12 or 13 digits.")

        try:
            raw = self._client().product.get(code, fields=self.FIELDS)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise FoodLookupError("Could not read data from Open Food Facts.") from error

        if not raw:
            return None
        return self._to_product(code, raw)

    # =========== Private Helpers ===========
    def _client(self):
        if self._api is None:
            self._api = openfoodfacts.API(user_agent=self._user_agent, timeout=self._timeout)
        return self._api

    def _to_product(self, code, raw):
        nutriments = raw.get("nutriments") or {}
        nutrition = {name: self._number(nutriments.get(field_name), factor) for name, (field_name, factor) in self.NUTRIENTS.items()}
        return FoodProduct(
            barcode=str(raw.get("code") or code),
            name=(raw.get("product_name") or "").strip() or "unknown product",
            brand=(raw.get("brands") or "").strip(),
            quantity=(raw.get("quantity") or "").strip(),
            ingredients=(raw.get("ingredients_text") or "").strip(),
            allergens=tuple(self._clean_tag(tag) for tag in (raw.get("allergens_tags") or [])),
            nutrition_per_100g=nutrition,
        )

    @staticmethod
    def _clean_tag(tag):
        return str(tag).split(":", 1)[-1].replace("-", " ") # remove language prefix - "en:tree-nuts" to "tree nuts"

    @staticmethod
    def _number(value, factor):
        try:
            return round(float(value) * factor, 3)
        except (TypeError, ValueError):
            return None
