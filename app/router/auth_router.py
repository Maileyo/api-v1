from fastapi import APIRouter, Request, Response, HTTPException
from pydantic import BaseModel
from app.controller.auth_controller import signInController,CreateAccountController , getCookiesController, signUpController , getUserController,checkUserController
from app.utils.apiResponse import success_response, error_response
from app.utils.error import handle_unauthenticated_error
from app.utils.token import verify_access_token
from app.utils.database import users_collection
from app.model.user import User
import logging
from app.utils.session import clear_session_cookie
from fastapi.responses import RedirectResponse
from app.service.auth.auth_service import  generate_google_login_url,generate_msft_login_url
from typing import List



router = APIRouter()



class SignUpRequest(BaseModel):
    userId: str
    name: str
    avatar: str

class SignInRequest(BaseModel):
    userId: str

class AuthProviderRequest(BaseModel):
    authProvider: List[str]



@router.get("/api/v1/cookies")
async def cookies(request: Request):
    try:
        user = await getCookiesController(request)
        return success_response(message="user already logged in",status_code=200,data=user)
            # for url in redirect_url:
            #     return RedirectResponse(url=url)
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)



@router.post("/api/v1/url-generate")
async def urlGenerate(request_data: AuthProviderRequest, request: Request, response: Response):
    try:
        authProvider = request_data.authProvider
        redirect_urls = []

        for provider in authProvider:
            if provider == "google":
                redirect_urls.append(generate_google_login_url())
            elif provider == "msft":
                redirect_urls.append(generate_msft_login_url())
        
        return success_response(message="Generated URLs", status_code=200, data=redirect_urls)

    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in urlGenerate: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)



@router.post("/api/v1/create-account")
async def createAccount(sign_up_request: SignUpRequest, request: Request, response: Response):
    try:
        user = await CreateAccountController(sign_up_request,response)
        json_response = success_response(message="user created",status_code=201,data=user)
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                json_response.headers[key] = value
        return json_response
    
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)
    
    
    
@router.post("/api/v1/signIn")
async def signIn(sign_in_request: SignInRequest, request: Request, response: Response):
    try:
        user = await signInController(sign_in_request,response)
        json_response = success_response(message="user logged in",status_code=200,data=user)
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                json_response.headers[key] = value
        return json_response
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)
    
    
    
@router.get("/auth/msft/callback")
async def msft_callback(request:Request, response: Response, code: str):
    try:
        # print(user_data)
        user = await signUpController(code,'msft',request,response)
        json_response = success_response(message="user created",status_code=201,data=user)
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                json_response.headers[key] = value
        return json_response
 
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)


@router.get("/auth/callback")
async def google_callback(request:Request, response: Response, code: str):
    try:
        # print(user_data)
        user = await signUpController(code,'google',request,response)
        json_response = success_response(message="user created",status_code=201,data=user)
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                json_response.headers[key] = value
        return json_response
 
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)



@router.get("/api/v1/get_user")
async def getUser(request: Request):
    try:
        user = await getUserController(request)
        return success_response(message="user found",status_code=200,data=user)
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)


@router.get("/api/v1/logout")
async def logout(response: Response):
    try:
        clear_session_cookie(response)
        json_response =  success_response(message="user logged out",status_code=200,data={})
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                json_response.headers[key] = value
        return json_response
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)
    
    
@router.get("/api/v1/check-user")    
async def checkUserExist(userId: str,request: Request):
    try:
        user = await checkUserController(userId)
        return success_response(message="user found",status_code=200,data=user)
    except HTTPException as he:
        return error_response(message=he.detail, status_code=he.status_code)
    except Exception as e:
        logging.error(f"Unexpected error in signIn: {str(e)}", exc_info=True)
        return error_response(message="Server error", status_code=500)