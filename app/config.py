import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
MONGODB_URI = os.getenv('MONGODB_URI')

MSFT_CLIENT_ID = os.getenv('MSFT_CLIENT_ID')
MSFT_CLIENT_SECRET = os.getenv('MSFT_CLIENT_SECRET')
MSFT_REDIRECT_URI = os.getenv('MSFT_REDIRECT_URI')

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')