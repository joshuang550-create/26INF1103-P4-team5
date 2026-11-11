"""Error hierarchy: every error the GUI can receive has a title and a description."""
import unittest

from models import errors


class ErrorTests(unittest.TestCase):
    def test_every_app_error_has_title_and_description(self):
        for name in ("InvalidInputError", "LoginFailedError", "InvalidActionError", "AIError", "AIConnectionError",
                     "AIResponseError", "DataError", "ConfigurationError", "UnexpectedError"):
            error = getattr(errors, name)()
            self.assertTrue(error.title and error.description, name)
            self.assertIsInstance(error, errors.SmartBiteError)

    def test_custom_description(self):
        self.assertEqual(errors.InvalidInputError("Age is wrong").description, "Age is wrong")

    def test_input_error_is_also_a_value_error(self):
        self.assertIsInstance(errors.InvalidInputError(), ValueError)

    def test_ai_errors_share_a_base_class(self):
        for cls in (errors.AIConnectionError, errors.AIServiceError, errors.AIResponseError):
            self.assertTrue(issubclass(cls, errors.AIError))

    def test_as_app_error_keeps_app_errors_and_hides_unknown_ones(self):
        known = errors.DataError()
        self.assertIs(errors.as_app_error(known), known)
        wrapped = errors.as_app_error(ZeroDivisionError("internal details"))
        self.assertIsInstance(wrapped, errors.UnexpectedError)
        self.assertNotIn("internal details", wrapped.description)  # raw exception text never reaches the user


if __name__ == "__main__":
    unittest.main()
