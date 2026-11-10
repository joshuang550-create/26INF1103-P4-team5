from models.errors import DataError, InvalidActionError
from progress.health_trend import HealthTrend


class ProgressTrackingEngine:
    """ Wraps AppEngine, rmbs verdict of every finished check
    
    Anyth not defined here is passed straight to wrapped engine,
    so GUI can use this exactly like an AppEngine."""


    def __init__(self, engine, verdict_log):
        self._engine = engine
        self._log = verdict_log
        self._food_name = "" # food of check in progress (answer_questions does not repeat it)

    # ========== Food Check ( same names as AppEngine) ==========
    def check_food(self, food_name, barcode =""):
        step = self._engine.check_food(food_name, barcode)
        self._food_name = food_name.strip()
        self._record(step)
        return step

    def answer_questions(self, answers):
        step = self._engine.answer_questions(answers)
        self._record(step)
        return step

    def delete_check(self):
        username = self._username()
        self._engine.delete_account()
        self._log.delete(username) # history gone when account gone

    # ========== New ==========
    def progress_trend(self):
        return HealthTrend(self._log.verdicts(self._username()))

    # ========== Everyth else goes to real engine ==========
    def __getattr__(self, name):
        return getattr(self._engine, name)

    # ========== Private Methods ==========
    def _username(self):
        profile = self._engine.profile
        if profile is None:
            raise InvalidActionError("No account logged in. Please log in first.")
        return profile.username

    def _record(self, step):
        outcome = step.outcome
        if outcome is None or outcome.severity is None: # still asking qn, or fallback (no verdict)
            return
        try:
            self._log.add(self._username(), self._food_name, outcome.severity.name)
        except DataError:
            pass # prob saving hist shldnt throw away result user wait for
