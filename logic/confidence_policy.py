from logic.response_action import ResponseAction


class ConfidencePolicy:
    def __init__(self, min_score=5.0, max_reprompts=1):
        self._min_score = min_score
        self._max_reprompts = max_reprompts

    def decide(self, score, attempt_number):
        if score >= self._min_score:
            return ResponseAction.ACCEPT # good enough

        if attempt_number < self._max_reprompts + 1:
            return ResponseAction.REPROMPT # not good enough, reprompt AI to try for better score

        return ResponseAction.FALLBACK # not good enough even after reprompt, use fallback response
