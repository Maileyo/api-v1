from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)
db = client['oauth_project']  # Replace 'oauth_project' with your actual DB name
users_collection = db['users']
