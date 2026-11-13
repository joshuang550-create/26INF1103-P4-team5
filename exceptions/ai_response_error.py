from exceptions.ai_error import AIError


class AIResponseError(AIError):
    title = "AI Answer Unusable"
    description = "The AI gave an answer the app could not use. Please try again."
