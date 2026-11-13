from dataclasses import dataclass


@dataclass(frozen=True)
class FoodCheckStep: # what the GUI gets back after running check_food and answer_questions
    questions: tuple = () # questions the AI needs answered first. empty when the check is finished
    outcome: object = None # an Outcome object when the check is finished, else None

    @property
    def needs_answers(self):
        return bool(self.questions) # True or False that it needs answers
