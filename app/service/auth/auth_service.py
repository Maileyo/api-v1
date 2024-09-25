from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.core.database import users_collection
from app.model.user import User
from bson import ObjectId
import os
import datetime
from googleapiclient.errors import HttpError
from app.config import MSFT_CLIENT_ID, MSFT_CLIENT_SECRET, MSFT_REDIRECT_URI,GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET

# Set up the Google OAuth client details
# GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
# GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/callback'


# Microsoft OAuth client details


print(GOOGLE_CLIENT_SECRET)
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
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "openid",
                "https://mail.google.com/"
            ]
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
    try:
        flow = get_google_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials


        if not credentials.token:
            raise HTTPException(status_code=401, detail="Failed to fetch access token")
        print(f"Token: {credentials.token}, Refresh Token: {credentials.refresh_token}, Expiry: {credentials.expiry}")

        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()

        return {
            "email": user_info["email"],
            "name": user_info["name"],
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry.timestamp() if credentials.expiry else None
        }
    except HttpError as error:
        print(f"An error occurred: {error}")
        raise HTTPException(status_code=401, detail="Failed to authenticate with Google")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# Refresh the access token if expired
async def refresh_access_token(email: str, refresh_token: str):
    credentials = Credentials(None, refresh_token=refresh_token, client_id=GOOGLE_CLIENT_ID, client_secret=GOOGLE_CLIENT_SECRET, token_uri='https://oauth2.googleapis.com/token')
    credentials.refresh(None)
    
    new_access_token = credentials.token
    expiry = credentials.expiry.timestamp()

    await update_user_tokens(email, new_access_token, refresh_token, expiry)
    return new_access_token



# msft login 
def generateMsftLoginUrl():
    client_id= MSFT_CLIENT_ID
    redirect_uri= MSFT_REDIRECT_URI
    scope="https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send offline_access"
    auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    query_params = {
    'client_id': client_id,
    'response_type': 'code',
    'redirect_uri': redirect_uri,
    'response_mode': 'query',
    'scope': scope,
     }
    authorization_url = f"{auth_url}?{urllib.parse.urlencode(query_params)}"
    
    
    
async def handle_msft_callback(code: str):
    try:
        code=code
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

        token_data = {
                'client_id': MSFT_CLIENT_ID,
                'scope': 'https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send offline_access',
                'code': code,
                'redirect_uri': MSFT_REDIRECT_URI,
                'grant_type': 'authorization_code',
                'client_secret': MSFT_CLIENT_SECRET,
            }

        response = requests.post(token_url, data=token_data)
        tokens = response.json()

        return {
            "email": "pranjal@gmail.com",
            "name": "pranjal",
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_expiry": tokens.expires_in.timestamp() if credentials.expiry else None
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
