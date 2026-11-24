class ReportError(Exception):
    def __init__(self, message, status_code=422):
        self.status_code = status_code
        super().__init__(message)
