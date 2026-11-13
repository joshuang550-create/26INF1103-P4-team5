from logic.outcomes.outcome import Outcome


class RecommendationOutcome(Outcome):
    def __init__(self, recommendations):
        self._recommendations = [dict(item) for item in recommendations] # list of dicts [{"food": "Milk", "reason": "The calcium is good for your bones"}, {"": "", "": ""}]

    @property
    def headline(self):
        return "UNDETERMINED"

    @property
    def severity(self):
        return None

    def details(self):
        return {
            "message": "We are unable to confidently determine whether this food suits you.",
            "recommendations": self._recommendations
        }
