"""Error handling for your existing Gemini AI Manager.

Integration in ai_manager.py:
1. Keep this file beside ai_manager.py and openfoodfacts_prompt.py.
2. Add: from ai_manager_error_handling import send_validated
3. Delete the old send_message() and send_validated() definitions.
   assess_food() can keep calling send_validated(chat, history, message).
4. Configure file logging once in main(), before processing records:

       import logging
       logging.basicConfig(
           filename="ai_manager_errors.log",
           level=logging.WARNING,
           format="%(asctime)s %(name)s %(levelname)s: %(message)s",
           encoding="utf-8",
       )

5. Create your Gemini client with a timeout and one SDK attempt, so the
   retry loop below owns the retry budget:

       client = genai.Client(
           api_key=load_decrypted_api_key(),
           http_options=types.HttpOptions(
               timeout=30000,
               retry_options=types.HttpRetryOptions(attempts=1),
           ),
       )

Contract: validated dictionary on success; None on failure. The caller handles
display and saving. This module has no input(), print(), file writes, custom
classes, or food/business decisions. Logging is configured by the application.

The default is three attempts TOTAL per send_validated call (one initial
attempt plus two retries), shared by API failures and malformed responses.
Your assess_food() may make further calls for separate follow-up questions.
HTTP 429 returns None immediately: the caller can retry after its rate/quota
limit is resolved. Retrying immediately may consume more of the same quota.

This patch handles sending/parsing/validation, not failures while loading key
files, initializing the client, building prompts, or saving records.

References:
https://googleapis.github.io/python-genai/#error-handling
https://ai.google.dev/gemini-api/docs/troubleshooting
"""

import json
import logging
import time

import httpx
from google.genai import errors

from openfoodfacts_prompt import SCHEMA, validate_response


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

# Technical retry policy, not food assessment/business logic.
RETRYABLE_STATUS_CODES = {408, 500, 502, 503, 504}


def send_validated(chat, history, message, max_retries=2):
    """Send, parse, validate, and return a dictionary or None.

    history is the existing mutable list supplied by the calling program.
    Only accepted exchanges are appended; rejected outputs are never saved
    to that list as successful answers. API/network retries resend the same
    message. Malformed-output retries include the original request and schema.
    """
    if type(max_retries) is not int or max_retries < 0:
        LOGGER.error("max_retries must be a non-negative integer.")
        return None

    total_attempts = max_retries + 1
    original_message = message
    repair_message = (
        original_message
        + "\n\nYour previous response was empty or did not match the required "
        "JSON schema. Answer the original request above again. Return one "
        "JSON object, without Markdown fences or extra text. Use a non-empty "
        "reason. For complete, information_needed must be empty; for "
        "needs_follow_up, include at least one non-empty question.\nSchema:\n"
        + json.dumps(SCHEMA)
    )

    for attempt in range(total_attempts):
        try:
            # The API call is INSIDE try, so its errors are caught below.
            response = chat.send_message(message)
            response_text = (response.text or "").strip()
            data = json.loads(response_text)

        except errors.APIError as exc:
            # Log technical details only, not full prompts or API responses.
            LOGGER.warning(
                "Gemini API HTTP %s on attempt %s/%s.",
                exc.code, attempt + 1, total_attempts,
            )
            if exc.code == 429:
                LOGGER.error("Rate/quota limit reached; defer this request.")
                return None
            if exc.code not in RETRYABLE_STATUS_CODES:
                LOGGER.error(
                    "Request stopped: check API key, permissions, model or request settings."
                )
                return None
            # Keep message unchanged for a temporary API failure.

        except (httpx.TransportError, TimeoutError, ConnectionError) as exc:
            LOGGER.warning(
                "Gemini connection failure (%s) on attempt %s/%s.",
                type(exc).__name__, attempt + 1, total_attempts,
            )
            # Keep message unchanged for a network failure.

        except json.JSONDecodeError:
            LOGGER.warning(
                "Empty or invalid JSON on attempt %s/%s.",
                attempt + 1, total_attempts,
            )
            message = repair_message

        except Exception as exc:
            # Last-resort guard around this external call and response parsing.
            # Unknown failures stop instead of being retried blindly.
            # KeyboardInterrupt and SystemExit are deliberately not caught.
            LOGGER.error("Unexpected Gemini response failure (%s).", type(exc).__name__)
            return None

        else:
            if validate_response(data):
                now = int(time.time())
                history.extend([
                    {"role": "user", "text": original_message, "time": now},
                    {"role": "model", "text": response_text, "time": now},
                ])
                return data

            LOGGER.warning(
                "JSON failed schema validation on attempt %s/%s.",
                attempt + 1, total_attempts,
            )
            message = repair_message

        if attempt < total_attempts - 1:
            # Default waits are 1 second, then 2 seconds. No wait after failure
            # of the final attempt. Cap delays if a larger budget is supplied.
            delay = 2 ** min(attempt, 3)
            LOGGER.warning("Retrying Gemini in %s second(s).", delay)
            time.sleep(delay)

    LOGGER.error("No valid Gemini response after %s attempts.", total_attempts)
    return None
