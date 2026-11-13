from enum import Enum


class ResponseAction(Enum):
    ACCEPT = "accept"
    REPROMPT = "reprompt"
    FALLBACK = "fallback"
    AVOID = "avoid"
