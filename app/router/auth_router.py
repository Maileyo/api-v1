from fastapi import APIRouter, Request, Response, HTTPException
from app.service.auth.auth_service import (
    generate_google_login_url,
    handle_google_callback,
    get_user_by_session_id,
    get_user_by_email,
    refresh_access_token,
    create_user,
)
from app.core.sessions import set_session_cookie, get_session_cookie, clear_session_cookie, create_session_id
from app.model.user import User

router = APIRouter()

@router.get("/login/google")
async def google_login(response: Response):
    # Generate a new session ID and set it in the cookie
    session_id = create_session_id()
    set_session_cookie(response, session_id)
    return {"login_url": generate_google_login_url()}

@router.get("/callback")
async def google_callback(request: Request, response: Response, code: str):
    # Retrieve session ID from the cookie
    session_id = get_session_cookie(request)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session not found")

    # Handle the Google OAuth callback and retrieve user data
    user_data = await handle_google_callback(code)
    
    if not user_data:
        raise HTTPException(status_code=400, detail="Invalid token or user data")

    user = await get_user_by_email(user_data['email'])
    if user:
        # Existing user, update tokens
        await refresh_access_token(user_data['email'], user_data['refresh_token'])
    else:
        # New user, create user in DB
        new_user = User(
            email=user_data['email'],
            name=user_data['name'],
            access_token=user_data['access_token'],
            refresh_token=user_data['refresh_token'],
            session_id=session_id,
            # Include token expiry if applicable
            token_expiry=user_data.get('token_expiry', None)  
        )
        await create_user(new_user)

    # Set the session cookie to link user session
    set_session_cookie(response, session_id)
    
    return {"message": "Logged in successfully", "user": user_data}

@router.get("/refresh-token")
async def refresh_token(request: Request):
    # Retrieve session ID from the cookie
    session_id = get_session_cookie(request)
    if not session_id:
        raise HTTPException(status_code=400, detail="Session not found")

    user = await get_user_by_session_id(session_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Refresh access token using the refresh token
    new_access_token = await refresh_access_token(user['email'], user['refresh_token'])
    return {"access_token": new_access_token}

@router.get("/logout")
async def logout(response: Response):
    # Clear the session cookie
    clear_session_cookie(response)
    return {"message": "Logged out successfully"}