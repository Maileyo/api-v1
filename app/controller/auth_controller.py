from app.utils.session import create_id, set_session_cookie, get_session_cookie, clear_session_cookie
from app.utils.token import verify_access_token,create_access_token
from app.utils.database import users_collection
from app.utils.error import handle_unauthenticated_error,handle_custom_error,handle_validation_error,handle_server_error,handle_not_found_error
from app.model.user import User,EmailAccount,Auth
from bson import ObjectId
from app.utils.error import APIException
import time 
from app.service.auth.auth_service import refresh_token,handle_google_callback,handle_msft_callback
from datetime import datetime, timedelta


async def getCookiesController(request):
    session_id = get_session_cookie(request)
    if not session_id:
        return  
        
    user_id = verify_access_token(session_id)
    
    user = await users_collection.find_one({"userId": user_id})
    if not user:
        return handle_not_found_error("user not found")
    
    # Initialize the email_acc list outside of the loop
    email_acc = []
    len(email_acc)   
    for email_account in user['email_account']:
        print("loop1")
        expiry_value = email_account['auth']['expiry']
        provider = email_account['provider']
        current_time = datetime.utcnow()
        
        # Check if the token is still valid
        if current_time > expiry_value:
            email_acc.append({
                "userId": user_id,
                "emailId": email_account['email_id'],
                "provider": email_account['provider'],
                "refresh_token": email_account['auth']['refresh_token']
            })
            
    token_status = await refresh_token(email_acc)
            # Call refresh_token for each email account that requires a refresh
    print("token_status",token_status)
    len(email_acc)      
   
    
    return {
        "userId": user['userId'],
        "name": user['name'],
        "avatar": user['avatar'],
        "token_status": token_status
    }



async def signInController(request_body, response):
    userId = request_body.userId
    if not userId:
        return handle_validation_error("user_ID is required")
    user = await users_collection.find_one({"userId": userId})
    if not user:
        return handle_custom_error("user not found", 404) 
    
    
    email_acc = []
    len(email_acc)   
    for email_account in user['email_account']:
        print("loop1")
        expiry_value = email_account['auth']['expiry']
        provider = email_account['provider']
        current_time = datetime.utcnow()
        
        # Check if the token is still valid
        if current_time > expiry_value:
            email_acc.append({
                "userId": userId,
                "emailId": email_account['email_id'],
                "provider": email_account['provider'],
                "refresh_token": email_account['auth']['refresh_token']
            })
            
    token_status = await refresh_token(email_acc)
            # Call refresh_token for each email account that requires a refresh
    print("token_status",token_status)
    len(email_acc)      
   
    jwt_access_token = create_access_token(data={"sub": user['userId']})
    set_session_cookie(response, jwt_access_token)
    return {
        "userId": user['userId'],
        "name": user['name'],
        "avatar": user['avatar'],
        "token_status": token_status
    }



async def signUpController(code: str, pdvr: str, request, response):
    try:
        # Handle OAuth callback based on provider
        if pdvr == "google":
            user_data = await handle_google_callback(code)
        elif pdvr == "msft":
            user_data = await handle_msft_callback(code)
            print(user_data)
        else:
            raise handle_custom_error(status_code=400, detail="Unsupported provider")
    except APIException as e:
        return handle_custom_error(e, status_code=500)
    except Exception as e:
        return handle_custom_error("Failed to authenticate user", 500)
    session_id = get_session_cookie(request)
    if not session_id:
             return  
    user_id =  verify_access_token(session_id)
    print(user_id)
    # user = await users_collection.find_one({"userId": user_id})
    # if not user:
    #         return handle_not_found_error("user not found")
    # print(user)
    # Check if the user already exists in the database
    existing_user = await users_collection.find_one({"userId": user_id})

    if existing_user:
        # User exists, check if the provider is already in the account list
        for email_account in existing_user["email_account"]:
            if email_account["provider"] == pdvr:
                return handle_custom_error(f"User already linked with {pdvr}", 409)
        
        expiration_time = datetime.utcnow() + timedelta(seconds=user_data['expiry'])

        # Append new email account details to existing user
        new_email_account = EmailAccount(
            email_id=user_data['email_id'],
            provider=user_data['provider'],
            auth=Auth(
                expiry= expiration_time,
                access_token=user_data['access_token'],
                refresh_token=user_data['refresh_token']
            )
        )

        # Update the user with the new provider's email account
        if existing_user["email_account"][0]["email_id"] == "":
            # If the user has an empty email account, remove it
            await users_collection.update_one(
                {"_id": existing_user["_id"]},
                {"$set": {"email_account": []}}
            )

    # Then, add the new email account
        await users_collection.update_one(
            {"_id": existing_user["_id"]},
            {"$push": {"email_account": new_email_account.dict()}}
        )

        # Create a new JWT access token and set the session cookie
        # jwt_access_token = create_access_token(data={"sub": existing_user['userId']})
        # set_session_cookie(response, jwt_access_token)

        return {
            "userId": existing_user['userId'],
            "name": existing_user['name'],
            "avatar": existing_user['avatar'],
        }

    return handle_custom_error("User not found", 404)
           
           
           
async def CreateAccountController(request_body,response):
    userId = request_body.userId
    name = request_body.name
    if not userId:
        return handle_validation_error("userId is required")
    if not name:
        return handle_validation_error("name is required")
    user = await users_collection.find_one({"userId": userId})
    print(user)
    if user:
        return handle_custom_error("user already exists", 409)
    expiration_time = datetime.utcnow()
    user = User(
        userId=userId,
        name=name,  
        avatar="",  
        email_account=[
            EmailAccount(
                email_id="",
                provider="",
                auth=Auth(
                    expiry= expiration_time,
                    access_token="",
                    refresh_token=""
                )
            )
        ]
    )
    user_data = user.dict()
    user_data['_id'] = ObjectId()
    try:
        await users_collection.insert_one(user_data)
    except Exception as e:
        return handle_server_error("failed to create user")
    
     # Create a JWT access token for the user
    jwt_access_token = create_access_token(data={"sub": user_data['userId']})
    
    # Set the session cookie with the JWT access token
    set_session_cookie(response, jwt_access_token)
    return {
        "userId": user_data['userId'],
        "name": user_data['name'],
        "avatar": user_data['avatar'],
    }

            
           
async def getUserController(request):
        session_id = get_session_cookie(request)
        if not session_id:
             return  handle_unauthenticated_error()
    
        user_id =  verify_access_token(session_id)
        user = await users_collection.find_one({"userId": user_id})
        if not user:
            return handle_not_found_error("user not found")
        print(user)
        response_data = {
            "userId": user['userId'],
            "name": user['name'],
            "avatar": user['avatar'],
        }
        return response_data


