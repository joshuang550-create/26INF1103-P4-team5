"""Barcode validation and Open Food Facts parsing, using a fake API (no internet)."""
import unittest
from types import SimpleNamespace

from services.openfoodfacts.food_lookup_error import FoodLookupError
from services.openfoodfacts.openfoodfacts_searcher import OpenFoodFactsSearcher


def searcher_returning(raw=None, error=None):
    def get(code, fields):
        if error:
            raise error
        return raw
    return OpenFoodFactsSearcher(api=SimpleNamespace(product=SimpleNamespace(get=get)))


FULL_RECORD = {
    "code": "5000112637922", "product_name": " Tomato Soup ", "brands": "SoupCo", "quantity": "400 g",
    "ingredients_text": "tomatoes, salt, sugar", "allergens_tags": ["en:celery", "en:tree-nuts"],
    "nutriments": {"sodium_100g": 0.5, "sugars_100g": 4.2, "saturated-fat_100g": 0.3, "trans-fat_100g": None},
}


class BarcodeValidationTests(unittest.TestCase):
    def test_valid_lengths(self):
        for code in ("12345678", "123456789012", "1234567890123", " 12345678 "):
            self.assertTrue(OpenFoodFactsSearcher.is_valid_barcode(code), code)

    def test_invalid_barcodes(self):
        for code in ("", "1234567", "123456789", "12345678901234", "abcdefgh", "1234-5678", "１２３４５６７８", None):
            self.assertFalse(OpenFoodFactsSearcher.is_valid_barcode(code), repr(code))

    def test_search_refuses_invalid_barcode(self):
        with self.assertRaises(ValueError):
            searcher_returning(FULL_RECORD).search("123")


class SearchTests(unittest.TestCase):
    def test_record_is_converted_to_a_product(self):
        product = searcher_returning(FULL_RECORD).search("5000112637922")
        self.assertEqual((product.name, product.brand, product.quantity), ("Tomato Soup", "SoupCo", "400 g"))
        self.assertEqual(product.ingredients, "tomatoes, salt, sugar")
        self.assertEqual(product.allergens, ("celery", "tree nuts"))  # language prefix removed

    def test_units_are_converted_to_the_apps_nutrient_keys(self):
        nutrition = searcher_returning(FULL_RECORD).search("5000112637922").nutrition_per_100g
        self.assertEqual(nutrition["sodium_mg"], 500.0)  # grams -> milligrams
        self.assertEqual(nutrition["sugar_g"], 4.2)
        self.assertEqual(nutrition["saturated_fat_g"], 0.3)
        self.assertIsNone(nutrition["trans_fat_g"])  # unknown stays unknown, not zero

    def test_unknown_product_returns_none(self):
        self.assertIsNone(searcher_returning(None).search("12345678"))
        self.assertIsNone(searcher_returning({}).search("12345678"))

    def test_sparse_record_gets_safe_defaults(self):
        product = searcher_returning({"code": "12345678"}).search("12345678")
        self.assertEqual((product.name, product.brand, product.ingredients, product.allergens), ("unknown product", "", "", ()))
        self.assertTrue(all(value is None for value in product.nutrition_per_100g.values()))

    def test_garbage_numbers_become_none(self):
        record = {"code": "12345678", "nutriments": {"sodium_100g": "lots", "sugars_100g": "n/a"}}
        nutrition = searcher_returning(record).search("12345678").nutrition_per_100g
        self.assertIsNone(nutrition["sodium_mg"])
        self.assertIsNone(nutrition["sugar_g"])

    def test_network_problems_become_food_lookup_error(self):
        for error in (OSError("offline"), ValueError("bad json"), KeyError("x"), TypeError("x")):
            with self.assertRaises(FoodLookupError, msg=repr(error)):
                searcher_returning(error=error).search("12345678")

    def test_lookup_error_has_user_facing_text(self):
        error = FoodLookupError()
        self.assertTrue(error.title and error.description)


if __name__ == "__main__":
    unittest.main()
