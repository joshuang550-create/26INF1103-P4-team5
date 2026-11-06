from abc import ABC, abstractmethod
from dataclasses import dataclass

from google import genai
from google.genai import errors, types
import httpx

from models.errors import SmartBiteError, AIError, AIConnectionError, AIServiceError, AIResponseError


# =========== Helper Type ===========
@dataclass(frozen=True)
class ModelResponse:
    text: str # the most recent response from the AI
    history: list # chat history of the user [{}, {}, {}]


# =========== Interface ===========
class AIModel(ABC):
    @abstractmethod
    def send(self, prompt, history, system_instruction): # system_instruction is a string that gets sent automatically to the ai with the prompt, basically rules for the ai to follow
        pass # returns ModelResponse object


# =========== AI Models ===========
class Gemini(AIModel):
    def __init__(self, api_key_supplier, model="gemini-3.5-flash-lite"):
        self._api_key_supplier = api_key_supplier # this will be provided during app build, api_key_supplier=data_manager_instance.get_api_key
        self._model = model

    def send(self, prompt, history, system_instruction): # history will be taken from AIManager data_manager.get_chat_history(username)
        try:
            api_key = self._api_key_supplier()

            history_content = [types.Content(role=item["role"], parts=[types.Part.from_text(text=item["text"])]) for item in history] # convert history to content
            retry_config = types.HttpRetryOptions(attempts=2, initial_delay=2.0, max_delay=32.0, http_status_codes=[408, 500, 502, 503, 504]) # will auto try to prompt again 2 times if these status codes are returned
            
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(retry_options=retry_config))
            chat = client.chats.create(model=self._model, history=history_content, config=types.GenerateContentConfig(system_instruction=system_instruction, response_mime_type="application/json")) # setup the chat "session"
            
            response = chat.send_message(prompt) # send the prompt and get a response

            if not response.text:
                raise AIResponseError() # if response is empty

            updated_history = chat.get_history(curated=True) # returns the whole history of the user, including history_content
            new_history = [{"role": item.role, "text": "".join(part.text or "" for part in (item.parts or []) if part.text is not None)} for item in updated_history] # convert content objects to dicts
            
            return ModelResponse(response.text, new_history)

        except SmartBiteError:
            raise # continues from an earlier raise like AIResponseError()

        except (httpx.ConnectError, httpx.TimeoutException) as error:
            raise AIConnectionError() from error

        except errors.APIError as error:
            raise AIServiceError(error.code) from error
            
        except Exception as error:
            raise AIError() from error
