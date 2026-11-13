from dataclasses import dataclass


@dataclass(frozen=True)
class Assessment:
    information_needed: list
    portion_g: float
    nutrients: dict
    reason: str
    potential_concern: bool
    confidence_score: int

    @property
    def needs_follow_up(self):
        return bool(self.information_needed)

    @property
    def confidence(self):
        return round(self.confidence_score / 10, 1)
