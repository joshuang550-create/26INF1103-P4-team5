from exceptions.smart_bite_error import SmartBiteError


class ConfigurationError(SmartBiteError):
    title = "Setup Problem"
    description = "SmartBite is not set up correctly."
