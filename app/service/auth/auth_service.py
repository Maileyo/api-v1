from fastapi import HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
# from app.core.database import users_collection
from app.model.user import User
from bson import ObjectId
import os
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from app.config import MSFT_CLIENT_ID, MSFT_CLIENT_SECRET, MSFT_REDIRECT_URI,GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET,GOOGLE_REDIRECT_URI
import requests
import urllib.parse
from app.utils.error import handle_unauthenticated_error,handle_custom_error,handle_validation_error,handle_server_error,handle_not_found_error
from app.utils.database import users_collection


def get_google_flow():
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
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
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        return flow
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# # Google OAuth login URL
def generate_google_login_url():
    flow = get_google_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return auth_url


# Refresh the access token for the given email account              
async def refresh_token(email_acc: []):
    print("email_dict", len(email_acc))
    
    refresh_results = []  # Collect results to return at the end

    for email in email_acc:
        result = {
            'emailId': email['emailId'],
            'provider': email['provider'],
            'status': 'failed',  # Default status
            'new_access_token': None
        }
        
        if email['provider'] == 'google':
            print("Refreshing Google token...")
            payload = {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                # 'refresh_token': "dssd",  # Ensure refresh_token is used
                'refresh_token': email['refresh_token'],  # Ensure refresh_token is used
                'grant_type': 'refresh_token'
            }
            try:
                response = requests.post("https://oauth2.googleapis.com/token", data=payload)
                token_info = response.json()
                if 'access_token' in token_info:
                    access_token = token_info['access_token']
                    expiry = datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                    
                    user_google = await users_collection.find_one({"userId": email['userId']})
                    print("New access token:", access_token)
                    
                    # Update the user's token info
                    for email_account in user_google["email_account"]:
                        if email_account["email_id"] == email['emailId']:
                            print("Old access token:", email_account["auth"]["access_token"])
                            email_account["auth"]["access_token"] = access_token
                            email_account["auth"]["expiry"] = expiry
                            await users_collection.update_one(
                                {"userId": email['userId']},
                                {"$set": {"email_account": user_google["email_account"]}}
                            )
                            result['status'] = 'success'
                            result['new_access_token'] = access_token
                else:
                    print("Failed to refresh Google token:", token_info)
                    result['error'] = token_info.get('error', 'Unknown error')

            except Exception as e:
                print(f"Error refreshing Google token: {str(e)}")
                result['error'] = str(e)

        elif email['provider'] == 'msft':
            print("Refreshing Microsoft token...")
            payload = {
                'client_id': MSFT_CLIENT_ID,
                'client_secret': MSFT_CLIENT_SECRET,
                'refresh_token': email['refresh_token'],
                # 'refresh_token': "dsds",
                'grant_type': 'refresh_token'
            }
            try:
                response = requests.post("https://login.microsoftonline.com/common/oauth2/v2.0/token", data=payload)
                token_info = response.json()
                if 'access_token' in token_info:
                    access_token = token_info['access_token']
                    expiry = datetime.utcnow() + timedelta(seconds=token_info.get('expires_in', 3600))
                    
                    user_msft = await users_collection.find_one({"userId": email['userId']})
                    print("New access token:", access_token)
                    
                    # Update the user's token info
                    for email_account in user_msft["email_account"]:
                        if email_account["email_id"] == email['emailId']:
                            print("Old access token:", email_account["auth"]["access_token"])
                            email_account["auth"]["access_token"] = access_token
                            email_account["auth"]["expiry"] = expiry
                            await users_collection.update_one(
                                {"userId": email['userId']},
                                {"$set": {"email_account": user_msft["email_account"]}}
                            )
                            result['status'] = 'success'
                            result['new_access_token'] = access_token
                else:
                    print("Failed to refresh Microsoft token:", token_info)
                    result['error'] = token_info.get('error', 'Unknown error')

            except Exception as e:
                print(f"Error refreshing Microsoft token: {str(e)}")
                result['error'] = str(e)

        refresh_results.append(result)

    return refresh_results
                



def generate_msft_login_url():
    client_id = '7573a9c3-588d-4cd7-ab98-73587d6ff469'
    redirect_uri = 'http://localhost:8000/auth/msft/callback'  # Ensure this matches the redirect URI registered on Azure
    scope = 'https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send  https://graph.microsoft.com/User.Read offline_access'
    auth_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    query_params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'response_mode': 'query',
        'scope': scope,
        'prompt':'consent'
    }

    authorization_url = f"{auth_url}?{urllib.parse.urlencode(query_params)}"
    return authorization_url  # Redirect the user to this URL


async def handle_msft_callback(ex_code:str):
        code = ex_code
        token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
        token_data = {
            'client_id': '7573a9c3-588d-4cd7-ab98-73587d6ff469',
            'scope': 'https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send  https://graph.microsoft.com/User.Read offline_access',
            'code': code,
            'redirect_uri': 'http://localhost:8000/auth/msft/callback',
            'grant_type': 'authorization_code',
            'client_secret': 'I-78Q~9Q.TzGOtSRyh_7d45fVWNEfkcRbhhHyaXR',
        }
        response_token = requests.post(token_url, data=token_data)
        tokens = response_token.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in')
        
        if not access_token:
            return handle_not_found_error("Access token not found")
        
        
        headers = {
        'Authorization': f'Bearer {access_token}'
            }
        me_url = 'https://graph.microsoft.com/v1.0/me'
        response_user = requests.get(me_url, headers=headers)
        user = response_user.json()
        userPrincipalName = user.get('userPrincipalName')
        if response_user.status_code == 200:
            return  {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expiry': expires_in,
            'email_id': userPrincipalName,
            'provider': 'msft'
                    }
        else:
           return handle_custom_error(message="Failed to fetch user data",status_code=400)



async def handle_google_callback(code: str):
    flow = get_google_flow()
    
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return handle_custom_error(message=str(e),status_code=400)

    credentials = flow.credentials
    access_token = credentials.token
    refresh_token = credentials.refresh_token
    expiry = credentials.expiry.timestamp()

    service = build('oauth2', 'v2', credentials=credentials)
    
    try:
        user_info = service.userinfo().get().execute()
    except Exception as e:
        return handle_custom_error(message=str(e),status_code=400)
    
    return {
        "email_id": user_info["email"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expiry": expiry,
        "provider": "google"
    }
