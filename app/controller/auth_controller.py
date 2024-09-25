from app.utils.session import create_id, set_session_cookie, get_session_cookie, clear_session_cookie
from app.utils.token import verify_access_token
from app.utils.database import users_collection
from app.utils.error import handle_unauthenticated_error,handle_custom_error,handle_validation_error
from app.model.user import User

async def getCookiesController(request: Request):
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

    
async def signInController(request: Request):
    try:
        userName =  request.name
        if not userName:
            return  handle_validation_error()
        if userName in users_collection.find_one({"name":userName})
            return handle_custom_error("user already exists",404)
        
        new_user = User(
            userId=user_data['userId'],
            name=user_data['name'],
            avatar=user_data['avatar'],
        email_account=[
            EmailAccount(
                email_id=email['email_id'],
                provider=email['provider'],
                auth=Auth(
                expiry=email['auth']['expiry'],
                access_token=email['auth']['access_token'],
                refresh_token=email['auth']['refresh_token']
                    )
                ) for email in user_data['email_account']
            ]
        )
        #  correct this 
        user_data_dict = new_user.dict()
        user_data_dict['_id'] = ObjectId()
        await users_collection.insert_one(user_data_dict)

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