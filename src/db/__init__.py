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

async def ping_mongodb(db: AsyncIOMotorDatabase):
    try:
        new_ping = await db["health"].insert_one({})
        if new_ping is None:
            raise "The ping object couln't be created"
        created_ping = await db["health"].find_one({
            "_id": new_ping.inserted_id
        })
        if created_ping is not None:
            return
        raise "The ping object couldn't be recovered"
    except Exception as e:
        raise f"Something went wrong with the database:\n{e}"
        
    