"""Error hierarchy: every error the GUI can receive has a title and a description."""
import unittest

from exceptions.invalid_input_error import InvalidInputError
from exceptions.ai_connection_error import AIConnectionError
from exceptions.ai_service_error import AIServiceError
from exceptions.ai_response_error import AIResponseError
from exceptions.ai_error import AIError
from exceptions.data_error import DataError
from exceptions.unexpected_error import UnexpectedError
from exceptions.as_app_error import as_app_error

class ErrorTests(unittest.TestCase):
    def test_custom_description(self):
        self.assertEqual(InvalidInputError("Age is wrong").description, "Age is wrong")

    def test_input_error_is_also_a_value_error(self):
        self.assertIsInstance(InvalidInputError(), ValueError)

    def test_ai_errors_share_a_base_class(self):
        for cls in (AIConnectionError, AIServiceError, AIResponseError):
            self.assertTrue(issubclass(cls, AIError))

    def test_as_app_error_keeps_app_errors_and_hides_unknown_ones(self):
        known = DataError()
        self.assertIs(as_app_error(known), known)
        wrapped = as_app_error(ZeroDivisionError("internal details"))
        self.assertIsInstance(wrapped, UnexpectedError)
        self.assertNotIn("internal details", wrapped.description)  # raw exception text never reaches the user


if __name__ == "__main__":
    unittest.main()
