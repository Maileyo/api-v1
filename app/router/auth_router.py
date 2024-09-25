from fastapi import APIRouter, Request, Response
# from app.service.auth.auth_service import (
#     generate_google_login_url,
#     handle_google_callback,
#     get_user_by_session_id,
#     get_user_by_email,
#     refresh_access_token,
#     create_user,
# )
# from app.core.sessions import set_session_cookie, get_session_cookie, clear_session_cookie, create_session_id
# from app.model.user import User

router = APIRouter()

# # Google auth 

# @router.get("/login/google")
# async def google_login(response: Response):
#     # Generate a new session ID and set it in the cookie
#     session_id = create_session_id()
#     set_session_cookie(response, session_id)
#     return {"login_url": generate_google_login_url()}


# @router.get("/callback")
# async def google_callback(request: Request, response: Response, code: str):
#     # Retrieve session ID from the cookie
#     session_id = get_session_cookie(request)
#     if not session_id:
#         raise HTTPException(status_code=400, detail="Session not found")

#     # Handle the Google OAuth callback and retrieve user data
#     user_data = await handle_google_callback(code)
    
#     if not user_data:
#         raise HTTPException(status_code=400, detail="Invalid token or user data")

#     user = await get_user_by_email(user_data['email'])
#     if user:
#         # Existing user, update tokens
#         await refresh_access_token(user_data['email'], user_data['refresh_token'])
#     else:
#         # New user, create user in DB
#         new_user = User(
#             email=user_data['email'],
#             name=user_data['name'],
#             access_token=user_data['access_token'],
#             refresh_token=user_data['refresh_token'],
#             session_id=session_id,
#             # Include token expiry if applicable
#             token_expiry=user_data.get('token_expiry', None)  
#         )
#         await create_user(new_user)

#     # Set the session cookie to link user session
#     set_session_cookie(response, session_id)
    
#     return {"message": "Logged in successfully", "user": user_data}

# @router.get("/refresh-token")
# async def refresh_token(request: Request):
#     # Retrieve session ID from the cookie
#     session_id = get_session_cookie(request)
#     if not session_id:
#         raise HTTPException(status_code=400, detail="Session not found")

#     user = await get_user_by_session_id(session_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
    
#     # Refresh access token using the refresh token
#     new_access_token = await refresh_access_token(user['email'], user['refresh_token'])
#     return {"access_token": new_access_token}



# msft auth
# @router.get("/login/msft")
# async def msft_login(response: Response):
#     # Generate a new session ID and set it in the cookie
#     session_id = create_session_id()
#     set_session_cookie(response, session_id)
#     return {"login_url": generateMsftLoginUrl()}



# @router.get("/auth/microsoft/callback")
# async def msft_callback(request: Request, response: Response, code: str):
#     # Retrieve session ID from the cookie
#     session_id = get_session_cookie(request)
#     if not session_id:
#         raise HTTPException(status_code=400, detail="Session not found")

#     # Handle the Google OAuth callback and retrieve user data
#     user_data = await handle_msft_callback(code)
    
#     if not user_data:
#         raise HTTPException(status_code=400, detail="Invalid token or user data")

#     user = await get_user_by_email(user_data['email'])
#     if user:
#         # Existing user, update tokens
#         await refresh_access_token(user_data['email'], user_data['refresh_token'])
#     else:
#         # New user, create user in DB
#         new_user = User(
#             email=user_data['email'],
#             name=user_data['name'],
#             access_token=user_data['access_token'],
#             refresh_token=user_data['refresh_token'],
#             session_id=session_id,
#             # Include token expiry if applicable
#             token_expiry=user_data.get('token_expiry', None)  
#         )
#         await create_user(new_user)

#     # Set the session cookie to link user session
#     set_session_cookie(response, session_id)
    
#     return {"message": "Logged in successfully", "user": user_data}







from app.controller.auth_controller import signInController , signUpController , getUserController
from app.utils.apiResponse import success_response, error_response
from app.utils.error import handle_unauthenticated_error
from app.utils.token import verify_access_token
from app.utils.database import users_collection

@router.get("/api/v1/signIn")
async def signIn(request: Request):
    try:
        user = await signInController(request)
        return success_response(user)
    
    except APIException as e:
        # Catch custom API exceptions and return error response
        return error_response(message=e.detail, status_code=e.status_code)
    
    except Exception as e:
        # Handle any unknown error with a generic server error response
        return error_response(message="An unexpected error occurred", status_code=500)

    
    
@router.post("/api/v1/signUp")
async def signUp(request: Request,response:Response):
    try:
        user =  signUpController(request)
        return success_response(user)

    except APIException as e:
        # Catch custom API exceptions and return error response
        return error_response(message=e.detail, status_code=e.status_code)
    
    except Exception as e:
        # Handle any unknown error with a generic server error response
        return error_response(message="An unexpected error occurred", status_code=500)


@router.get("/api/v1/get_user")
async def getUser(request: Request):
    try:
        user = await getUserController(request)
        return success_response(user)
        
    except APIException as e:
        # Catch custom API exceptions and return error response
        return error_response(message=e.detail, status_code=e.status_code)
    
    except Exception as e:
        # Handle any unknown error with a generic server error response
        return error_response(message="An unexpected error occurred", status_code=500)


@router.get("/api/v1/logout")
async def logout(response: Response):
    try:
        clear_session_cookie(response)
        return success_response("logged out successfully")
    except Exception as e:
        return error_response(f"error while logging out {e}",status_code=422)