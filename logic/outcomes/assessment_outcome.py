from logic.outcomes.outcome import Outcome


class AssessmentOutcome(Outcome): # used when confidence score is good enough or allergen detected
    def __init__(self, evaluation):
        self._evaluation = evaluation

    @property
    def headline(self):
        return self._evaluation.verdict.name

    @property
    def severity(self):
        return self._evaluation.verdict

    def details(self):
        assessment = self._evaluation.assessment
        return {
            "reason": assessment.reason, # long text from the ai on why the verdict
            "portion_g": assessment.portion_g, # the portion the nutrient amounts are based on
            "nutrients": dict(assessment.nutrients), 
            "flags": [{"nutrient": nutrient, "value": value, "level": level} for nutrient, value, level in self._evaluation.flags], 
            "allergens_found": {category: list(words) for category, words in self._evaluation.allergens_found.items()}, 
            "potential_concern": assessment.potential_concern, # true or false
            "confidence": assessment.confidence, # float 0 to 10
        }
