from exceptions.smart_bite_error import SmartBiteError


class InvalidInputError(SmartBiteError, ValueError): # also a ValueError so except ValueError will also work
    title = "Invalid Input"
    description = "Please check what you entered and try again."
