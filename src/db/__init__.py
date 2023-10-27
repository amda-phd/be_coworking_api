from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from decouple import config

MONGODB_URL = config('MONGODB_URL', cast=str)
MONGODB_NAME = config('MONGODB_NAME', cast=str)

# Initialize the MongoDB client and database
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

async def connect_to_mongodb():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_NAME]
    return db

async def close_mongodb_connection():
    if client:
        client.close()

async def ping_health():
    new_ping = await db["health"].insert_one({})
    created_ping = await db["health"].find_one({
        "_id": new_ping.inserted_id
    })
    if created_ping is not None:
        return True
    return False