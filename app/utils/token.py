from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.utils.error import handle_inv_token_error
from app.config import SECRET_KEY, ALGORITHM


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire=None
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            handle_inv_token_error()
        return user_id
    except JWTError:
        handle_inv_token_error()