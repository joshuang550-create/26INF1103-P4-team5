from exceptions.ai_error import AIError


class AIServiceError(AIError):
    title = "AI Service Error"
    description = "The AI service reported a problem. Please try again later."

    CODE_DESCRIPTIONS = {
        401: "The AI key was rejected. Check that your API key is valid.",
        403: "Access to the AI service was denied (permission or regional restriction).",
        429: "Too many requests, or the AI account is out of credits. Try again later.",
        500: "The AI service is temporarily down. Try again later.",
        503: "The AI service is temporarily down. Try again later.",
    }

    def __init__(self, code):
        self.code = code
        super().__init__(self.CODE_DESCRIPTIONS.get(code)) # None for unhandled codes
