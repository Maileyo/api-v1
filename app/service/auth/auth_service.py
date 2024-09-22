from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.core.database import users_collection
from app.model.user import User
from bson import ObjectId
import os
import datetime

# Set up the Google OAuth client details
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'

# Google OAuth Flow Setup
def get_google_flow():
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes="https://mail.google.com/"
        )
        flow.redirect_uri = REDIRECT_URI
        return flow
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Check if user exists in the database by session ID
async def get_user_by_session_id(session_id: str):
    return await users_collection.find_one({"session_id": session_id})

# Check if user exists by email (after OAuth login)
async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

# Store user in the database
async def create_user(user_data: User):
    user_data_dict = user_data.dict()
    user_data_dict['_id'] = ObjectId()
    await users_collection.insert_one(user_data_dict)

# Update the access and refresh tokens in the database
async def update_user_tokens(email: str, access_token: str, refresh_token: str, token_expiry: int):
    await users_collection.update_one(
        {"email": email},
        {"$set": {"access_token": access_token, "refresh_token": refresh_token, "token_expiry": token_expiry}}
    )

# Google OAuth login URL
def generate_google_login_url():
    flow = get_google_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

# Handle the callback and exchange code for tokens
async def handle_google_callback(code: str):
    flow = get_google_flow()
    flow.fetch_token(code=code)

    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    expiry = credentials.expiry.timestamp()

    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    
    return {
        "email": user_info["email"],
        "name": user_info["name"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": expiry
    }

# Refresh the access token if expired
async def refresh_access_token(email: str, refresh_token: str):
    credentials = Credentials(None, refresh_token=refresh_token, client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET, token_uri='https://oauth2.googleapis.com/token')
    credentials.refresh(None)
    
    new_access_token = credentials.token
    expiry = credentials.expiry.timestamp()

    await update_user_tokens(email, new_access_token, refresh_token, expiry)
    return new_access_token
