from exceptions.smart_bite_error import SmartBiteError


class InvalidActionError(SmartBiteError):
    title = "Action Not Available"
    description = "That action is not available right now."
