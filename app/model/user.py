from pydantic import BaseModel
from typing import List, Dict
class Auth(BaseModel):
    expiry: float
    access_token: str
    refresh_token: str

class EmailAccount(BaseModel):
    email_id: str
    provider: str
    auth: Auth

class User(BaseModel):
    userId: str
    name: str
    avatar: str
    email_account: List[EmailAccount]
