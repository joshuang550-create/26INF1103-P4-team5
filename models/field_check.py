from dataclasses import dataclass


@dataclass(frozen=True)
class FieldCheck:
    """ Result of checking one form field, made by IOManager and shown by HintLabel. """
    message: str = "" # hint to show next to the field, "" when the field is fine
    fix: str | None = None # corrected text the user can accept with one click, None when there is no suggestion