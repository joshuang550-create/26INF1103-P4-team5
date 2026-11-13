from exceptions.smart_bite_error import SmartBiteError


class DataError(SmartBiteError): # a data file is corrupted, or could not be read or saved
    title = "Data Error"
    description = "SmartBite could not read or save its data. Please try again."
