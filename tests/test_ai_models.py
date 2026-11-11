"""Gemini wrapper: every failure type is translated into the app's own errors. The Gemini client is mocked."""
import unittest
from types import SimpleNamespace
from unittest import mock

import httpx
from google.genai import errors

import models.ai_models as ai_models
from models.errors import AIConnectionError, AIError, AIResponseError, AIServiceError, ConfigurationError


class FakeApiError(errors.APIError):
    def __init__(self, code):  # skip the real constructor so this works with any library version
        Exception.__init__(self, f"api error {code}")
        self.code = code


def working_client(reply_text="{}"):
    client = mock.MagicMock()
    chat = client.chats.create.return_value
    chat.send_message.return_value = SimpleNamespace(text=reply_text)
    chat.get_history.return_value = [SimpleNamespace(role="user", parts=[SimpleNamespace(text="hello")]),
                                     SimpleNamespace(role="model", parts=[SimpleNamespace(text=reply_text)])]
    return client


class GeminiTests(unittest.TestCase):
    def send(self, client=None, client_error=None, key_supplier=lambda: "fake-key"):
        gemini = ai_models.Gemini(api_key_supplier=key_supplier)
        patch = mock.patch.object(ai_models.genai, "Client", side_effect=client_error) if client_error else \
            mock.patch.object(ai_models.genai, "Client", return_value=client)
        with patch:
            return gemini.send("prompt", [], "system rules")

    def test_successful_reply_and_history(self):
        response = self.send(working_client('{"ok": true}'))
        self.assertEqual(response.text, '{"ok": true}')
        self.assertEqual(response.history, [{"role": "user", "text": "hello"}, {"role": "model", "text": '{"ok": true}'}])

    def test_empty_reply_is_an_unusable_answer(self):
        with self.assertRaises(AIResponseError):
            self.send(working_client(""))

    def test_connection_problems(self):
        for error in (httpx.ConnectError("down"), httpx.TimeoutException("slow")):
            with self.assertRaises(AIConnectionError, msg=type(error).__name__):
                self.send(client_error=error)

    def test_service_errors_carry_a_helpful_message(self):
        with self.assertRaises(AIServiceError) as caught:
            self.send(client_error=FakeApiError(429))
        self.assertEqual(caught.exception.code, 429)
        self.assertIn("Too many requests", caught.exception.description)

    def test_unlisted_service_code_gets_default_message(self):
        with self.assertRaises(AIServiceError) as caught:
            self.send(client_error=FakeApiError(418))
        self.assertEqual(caught.exception.description, AIServiceError.description)

    def test_unexpected_failure_is_wrapped(self):
        with self.assertRaises(AIError):
            self.send(client_error=RuntimeError("boom"))

    def test_configuration_problem_is_passed_through_unchanged(self):
        def missing_key():
            raise ConfigurationError("no key")
        with self.assertRaises(ConfigurationError):
            self.send(key_supplier=missing_key)


if __name__ == "__main__":
    unittest.main()
