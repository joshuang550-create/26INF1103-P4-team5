class SmartBiteError(Exception):
    title = "Something went wrong"
    description = "An unexpected problem occurred. Please try again."

    def __init__(self, description=None):
        self.description = description or self.description # allows custom description
        super().__init__(self.description)
