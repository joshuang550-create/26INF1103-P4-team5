from exceptions.ai_error import AIError


class AIConnectionError(AIError):
    title = "No Connection"
    description = "Could not reach the AI service. Check your internet connection and try again."
