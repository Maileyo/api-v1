from pydantic import BaseModel

class User(BaseModel):
    email: str
    name: str
    access_token: str
    refresh_token: str
    session_id: str
    token_expiry: int  # Timestamp to track access token expiry
