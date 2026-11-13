from exceptions.smart_bite_error import SmartBiteError


class AIError(SmartBiteError):
    title = "AI Error"
    description = "The AI service failed unexpectedly. Please try again later."
