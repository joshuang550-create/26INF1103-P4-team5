"""Error hierarchy: every error the GUI can receive has a title and a description."""
import unittest

from exceptions.ai_connection_error import AIConnectionError
from exceptions.ai_error import AIError
from exceptions.ai_response_error import AIResponseError
from exceptions.ai_service_error import AIServiceError
from exceptions.as_app_error import as_app_error
from exceptions.configuration_error import ConfigurationError
from exceptions.data_error import DataError
from exceptions.invalid_action_error import InvalidActionError
from exceptions.invalid_input_error import InvalidInputError
from exceptions.login_failed_error import LoginFailedError
from exceptions.smart_bite_error import SmartBiteError
from exceptions.unexpected_error import UnexpectedError


class ErrorTests(unittest.TestCase):
    def test_every_app_error_has_title_and_description(self):
        for cls in (InvalidInputError, LoginFailedError, InvalidActionError, AIError, AIConnectionError,
                    AIResponseError, DataError, ConfigurationError, UnexpectedError):
            error = cls()
            self.assertTrue(error.title and error.description, cls.__name__)
            self.assertIsInstance(error, SmartBiteError)

    def test_custom_description(self):
        self.assertEqual(InvalidInputError("Age is wrong").description, "Age is wrong")

    def test_input_error_is_also_a_value_error(self):
        self.assertIsInstance(InvalidInputError(), ValueError)

    def test_ai_errors_share_a_base_class(self):
        for cls in (AIConnectionError, AIServiceError, AIResponseError):
            self.assertTrue(issubclass(cls, AIError))

    def test_service_error_uses_the_message_for_its_code(self):
        error = AIServiceError(429)
        self.assertEqual(error.code, 429)
        self.assertIn("Too many requests", error.description)

    def test_service_error_with_unlisted_code_gets_the_default_message(self):
        self.assertEqual(AIServiceError(418).description, AIServiceError.description)

    def test_as_app_error_keeps_app_errors_and_hides_unknown_ones(self):
        known = DataError()
        self.assertIs(as_app_error(known), known)
        wrapped = as_app_error(ZeroDivisionError("internal details"))
        self.assertIsInstance(wrapped, UnexpectedError)
        self.assertNotIn("internal details", wrapped.description)  # raw exception text never reaches the user


if __name__ == "__main__":
    unittest.main()
