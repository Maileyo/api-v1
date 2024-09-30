from fastapi import HTTPException

class APIException(HTTPException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=message)

def handle_not_found_error(message: str = "Resource not found"):
    raise APIException(message, status_code=404)

def handle_unauthenticated_error(message: str = "Unauthenticated"):
    raise APIException(message, status_code=401)

def handle_validation_error(message: str = "Validation Error"):
    raise APIException(message, status_code=422)

def handle_server_error(message: str = "Server Error"):
    raise APIException(message, status_code=500)


def handle_inv_token_error(message: str = "Invalid Token"):
    raise APIException(message, status_code=403)

def handle_custom_error(message: str,status_code):
    raise APIException(message, status_code)



