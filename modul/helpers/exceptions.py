class BadRequest(Exception):
    def __init__(self, message: str):
        self.message = message
        super(BadRequest, self).__init__(message)
