class SmartBiteError(Exception):
    title = "Something went wrong"
    description = "An unexpected problem occured. Please try again."

    def __init__(self, description=None):
        self.description = description or self.description # allows custom description
        super().__init__(self.description)


# =========== Input Errors ===========
class InvalidInputError(SmartBiteError, ValueError): # also a ValueError so except ValueError will also work
    title = "Invalid Input"
    description = "Please check what you entered and try again."


# =========== AI Errors ===========
class AIError(SmartBiteError):
    title = "AI Error"
    description = "The AI service failed unexpectedly. Please try again later."


class AIConnectionError(AIError):
    title = "No Connection"
    description = "Could not reach the AI service. Check your internet connection and try again."


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


class AIResponseError(AIError):
    title = "AI Answer Unusable"
    description = "The AI gave an answer the app could not use. Please try again."


# =========== OpenFoodFacts Error ===========
class FoodLookupError(Exception):
    title = "Barcode Lookup Failed"
    description = "Could not look up that barcode right now. You can continue without barcode data, or try again."


# =========== Data Errors ===========
class DataError(SmartBiteError): # a data file is corrupted, or could not be read or saved
    title = "Data Error"
    description = "SmartBite could not read or save its data. Please try again."


# =========== Setup Errors ===========
class ConfigurationError(SmartBiteError):
    title = "Setup Problem"
    description = "SmartBite is not set up correctly."


# =========== Unplanned Errors ===========
class UnexpectedError(SmartBiteError):
    pass # default title and description


# =========== Return Error Object ===========
def as_app_error(error):
    if hasattr(error, "title") and hasattr(error, "description"):
        return error # has title and description to be shown to user  
    return UnexpectedError() # has default title and description
