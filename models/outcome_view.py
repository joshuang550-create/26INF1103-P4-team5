from dataclasses import dataclass


@dataclass(frozen=True)
class OutcomeView:
    """ An Outcome turned into what the screen shows: a title, a colour and the text below it. """
    title: str
    colour: str
    text: str