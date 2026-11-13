from exceptions.smart_bite_error import SmartBiteError


class LoginFailedError(SmartBiteError):
    title = "Login Failed"
    description = "Please enter a valid username and password."
