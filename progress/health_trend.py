VERDICT_SCORES = {"OK": 100, "CAUTION": 50, "AVOID": 0}


class HealthTrend:
    """ Turns list of verdicts (oldest first) into scores and direction. """

    MIN_CHECKS = 4       # fewest checks before judging direction
    CHANGE_NEEDED = 10   # points of difference needed to call better or worse

    def __init__(self, verdicts, window=3):
        self._scores = [VERDICT_SCORES[verdict] for verdict in verdicts if verdict in VERDICT_SCORES]
        self._window = window

    @property
    def scores(self):
        return list(self._scores)

    def rolling_average(self):
        """ Each check: average and checks just before"""
        averages = []
        for index in range (len(self._scores)):
            recent = self._scores[max(0, index - self._window + 1):index + 1]
            averages.append(sum(recent) / len(recent))
        return averages

    def direction(self):
        """ Compare newer half with older half """
        if len(self._scores) < self.MIN_CHECKS:
            return "not enough data"

        half = len(self._scores) // 2
        earlier = sum(self._scores[:half]) / half
        recent = sum(self._scores[-half:]) / half

        if recent - earlier >= self.CHANGE_NEEDED:
            return "improving"
        if earlier - recent >= self.CHANGE_NEEDED:
            return "declining"
        return "steady"

    def summary(self):
        """ description of trend, when chart cannot be shown """
        total = len(self._scores)
        if total == 0:
            return "No food checks recorded. Start cheking to start progress history."
        if total < self.MIN_CHECKS:
            return (f"You have {total} food check{'' if total == 1 else 's'} so far."
                    "Check a few more to see how your choices are trending.")

        half = total // 2
        opening = {"improving": "Your food checks are improving.", 
                   "declining": "Your food checks are getting less helathy.",
                   "steady": "Your food checks have been steady"}[self.direction()]
        return (f"{opening} Your latest {half} checks had {self._counts_text(self._scores[-half:])}, "
                f"compared with {self._counts_text(self._scores[:half])} in your earliest {half}.")

    # ========== Private Methods ==========
    @staticmethod
    def _counts_text(scores):
        return (f"{scores.count(VERDICT_SCORES['OK'])} OK, "
                f"{scores.count(VERDICT_SCORES['CAUTION'])} CAUTION and "
                f"{scores.count(VERDICT_SCORES['AVOID'])} AVOID")