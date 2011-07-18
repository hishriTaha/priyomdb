class ServletError(Exception):
    def __init__(self, code, message=None):
        self.code = code
        self.message = message
        
class ServletInvalidQueryError(ServletError):
    def __init__(self, message = "Invalid query"):
        super(ServletInvalidQueryError, self).__init__(400, message)

