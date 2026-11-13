from abc import ABC, abstractmethod


class Outcome(ABC): # final output that the GUI can use
    @property
    @abstractmethod
    def headline(self):
        pass # OK, CAUTION, AVOID, UNDETERMINED

    @property
    @abstractmethod
    def severity(self):
        pass # Verdict

    @abstractmethod
    def details(self):
        pass # dict of details/info to show the user

    def to_dict(self):
        return {"headline": self.headline, "severity": None if self.severity is None else self.severity.name, "details": self.details()}
