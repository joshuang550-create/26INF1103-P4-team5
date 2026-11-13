from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    text: str # the most recent response from the AI
    history: list # chat history of the user [{}, {}, {}]
