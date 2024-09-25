from fastapi import Response, Request
import uuid

def create_id():
    return str(uuid.uuid4())  # Generate a unique session ID

def set_session_cookie(response: Response, session_id: str):
    response.set_cookie(key="session_id", value=session_id, httponly=True, secure=True)

def get_session_cookie(request: Request):
    return request.cookies.get("session_id")

def clear_session_cookie(response: Response):
    response.delete_cookie("session_id")