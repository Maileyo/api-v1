from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from googleapiclient.errors import HttpError
from app.model.user import User
from app.config import (
    MSFT_CLIENT_ID, MSFT_CLIENT_SECRET, MSFT_REDIRECT_URI, 
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
)
from app.utils.error import (
    handle_unauthenticated_error, handle_custom_error, 
    handle_validation_error, handle_server_error, handle_not_found_error
)
from app.utils.database import users_collection
from typing import List, Dict
import urllib.parse
import requests
import os

MSFT_SCOPES = "https://graph.microsoft.com/User.Read https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send offline_access"


# Helper function to generate Google OAuth flow
def get_google_flow():
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": GOOGLE_REDIRECT_URI,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=[
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://mail.google.com/",
                "openid"
            ]
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        return flow
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generate Google OAuth login URL
def generate_google_login_url():
    flow = get_google_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url

# Handle Google OAuth callback
async def handle_google_callback(code: str):
    flow = get_google_flow()
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return handle_custom_error(message=str(e), status_code=400)

    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    expiry = 3600  # Default expiry time in seconds

    service = build('oauth2', 'v2', credentials=credentials)
    try:
        user_info = service.userinfo().get().execute()
    except Exception as e:
        return handle_custom_error(message=str(e), status_code=400)

    return {
        "email_id": user_info["email"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expiry": expiry,
        "provider": "google"
    }

# Generate Microsoft OAuth login URL
def generate_msft_login_url():
    auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    query_params = {
        'client_id': MSFT_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': MSFT_REDIRECT_URI,
        'response_mode': 'query',
        'scope': MSFT_SCOPES,
        'prompt': 'consent'
    }
    authorization_url = f"{auth_url}?{urllib.parse.urlencode(query_params)}"
    return authorization_url

# Handle Microsoft OAuth callback
async def handle_msft_callback(ex_code: str):
    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    token_data = {
        'client_id': MSFT_CLIENT_ID,
        'scope': MSFT_SCOPES,
        'code': ex_code,
        'redirect_uri': MSFT_REDIRECT_URI,
        'grant_type': 'authorization_code',
        'client_secret': MSFT_CLIENT_SECRET
    }
    response_token = requests.post(token_url, data=token_data)
    tokens = response_token.json()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    expires_in = tokens.get('expires_in')

    if not access_token:
        return handle_not_found_error("Access token not found")

    headers = {'Authorization': f'Bearer {access_token}'}
    me_url = 'https://graph.microsoft.com/v1.0/me'
    response_user = requests.get(me_url, headers=headers)
    user = response_user.json()
    userPrincipalName = user.get('userPrincipalName')

    if response_user.status_code == 200:
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expiry': expires_in,
            'email_id': userPrincipalName,
            'provider': 'msft'
        }
    else:
        return handle_custom_error(message="Failed to fetch user data", status_code=400)
    

# Refresh the access token for a given email account

async def refresh_token(email_acc: List[Dict]):
    print("Refreshing tokens for", len(email_acc), "accounts")
    refresh_results = []  # Collect results to return at the end

    for email in email_acc:
        result = {
            'emailId': email['emailId'],
            'provider': email['provider'],
            'status': 'failed',  # Default status
            'new_access_token': None
        }

        if email['provider'] == 'google':
            result = await handle_google_refresh_token(email, result)
        elif email['provider'] == 'msft':
            result = await handle_msft_refresh_token(email, result)

        refresh_results.append(result)
    return refresh_results

# Handle Google token refresh
async def handle_google_refresh_token(email: Dict, result: Dict):
    print("Refreshing Google token...")
    payload = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'refresh_token': email['refresh_token'],
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post("https://oauth2.googleapis.com/token", data=payload)
        token_info = response.json()
        if 'access_token' in token_info:
            access_token = token_info['access_token']
            expiry = datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
            await update_user_token(email, access_token, expiry)
            result['status'] = 'success'
            result['new_access_token'] = access_token
        else:
            print("Failed to refresh Google token:", token_info)
            result['error'] = token_info.get('error', 'Unknown error')
    except Exception as e:
        print(f"Error refreshing Google token: {str(e)}")
        result['error'] = str(e)
    return result

# Handle Microsoft token refresh
async def handle_msft_refresh_token(email: Dict, result: Dict):
    print("Refreshing Microsoft token...")
    payload = {
        'client_id': MSFT_CLIENT_ID,
        'client_secret': MSFT_CLIENT_SECRET,
        'refresh_token': email['refresh_token'],
        'grant_type': 'refresh_token'
    }
    try:
        response = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=payload)
        token_info = response.json()
        if 'access_token' in token_info:
            access_token = token_info['access_token']
            expiry = datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
            await update_user_token(email, access_token, expiry)
            result['status'] = 'success'
            result['new_access_token'] = access_token
        else:
            print("Failed to refresh Microsoft token:", token_info)
            result['error'] = token_info.get('error', 'Unknown error')
    except Exception as e:
        print(f"Error refreshing Microsoft token: {str(e)}")
        result['error'] = str(e)
    return result

# Helper function to update user's access token and expiry
async def update_user_token(email: Dict, access_token: str, expiry: datetime):
    user_record = await users_collection.find_one({"userId": email['userId']})
    if user_record:
        for email_account in user_record["email_account"]:
            if email_account["email_id"] == email['emailId']:
                print("Updating access token for", email['emailId'])
                email_account["auth"]["access_token"] = access_token
                email_account["auth"]["expiry"] = expiry
        await users_collection.update_one(
            {"userId": email['userId']},
            {"$set": {"email_account": user_record["email_account"]}}
        )