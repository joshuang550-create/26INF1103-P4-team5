from abc import ABC, abstractmethod


class AIModel(ABC):
    @abstractmethod
    def send(self, prompt, history, system_instruction): # system_instruction is a string that gets sent automatically to the ai with the prompt, basically rules for the ai to follow
        pass # returns ModelResponse object
