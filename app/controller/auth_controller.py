from app.utils.session import create_id, set_session_cookie, get_session_cookie, clear_session_cookie
from app.utils.token import verify_access_token
from app.utils.database import users_collection
from app.utils.error import handle_unauthenticated_error,custom_error

def getCookiesController(request: Request):
    try:
        session_id = get_session_cookie(request)
        if not session_id:
             return  handle_unauthenticated_error()
    
        user_id =  verify_access_token(session_id)
        user = await users_collection.find_one({"userId": user_id})
        if not user:
            return handle_not_found_error("user not found")
        for email_account in user.email_account:
            expiry_value = email_account.auth.expiry
            provider = email_account.provider
            current_time = time.time()
            if current_time > expiry_value:
                # TODO: Refresh the token in the auth service
                # new_auth = refresh_token(provider, email_account.email_id)
                email_account.auth = new_auth
                return user
            else:
                return user
    except Exception as e:
        return handle_unauthenticated_error()