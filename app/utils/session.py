from fastapi import Response, Request
import uuid
import datetime

def create_id():
    return str(uuid.uuid4())  # Generate a unique session ID

def set_session_cookie(response: Response, session_id: str):
    expires = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=20)
    response.set_cookie(key="session_id", value=session_id, httponly=True, secure=False, expires=expires)

def get_session_cookie(request: Request):
    return request.cookies.get("session_id")

def clear_session_cookie(response: Response):
    response.delete_cookie("session_id")