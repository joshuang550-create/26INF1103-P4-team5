from exceptions.unexpected_error import UnexpectedError


def as_app_error(error):
    if hasattr(error, "title") and hasattr(error, "description"):
        return error # has title and description to be shown to user  
    return UnexpectedError() # has default title and description
