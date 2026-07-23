class AppError(Exception):
    """Raised by services for expected business-logic failures.

    Carries the HTTP status code the route should return, so routes never
    need to inspect the error message to decide on a status code.
    """

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
