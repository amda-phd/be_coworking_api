from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from mongomock_motor import AsyncMongoMockClient
from decouple import config

MONGODB_URL = config('MONGODB_URL', cast=str)
MONGODB_NAME = config('MONGODB_NAME', cast=str)

# Initialize the MongoDB client and database
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

def connect_to_mongodb(app, testing: bool = False):
    global client, db
    if testing:
        client = AsyncMongoMockClient()
    else:
        client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_NAME]
    if app:
        app.mongodb_client = client
        app.mongodb = db
    return db

def close_mongodb_connection(app):
    if app:
        client = app.mongodb_client
    if client:
        client.close()

async def ping_health(db: AsyncIOMotorDatabase):
    try:
        new_ping = await db["health"].insert_one({})
        created_ping = await db["health"].find_one({
            "_id": new_ping.inserted_id
        })
        if created_ping is not None:
            return True
        return False
    except Exception as e:
        print(f"Something went wrong with the database:\n{e}")
        return False
    