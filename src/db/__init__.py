from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from mongomock_motor import AsyncMongoMockClient
from decouple import config
from fastapi.encoders import jsonable_encoder

MONGODB_HOST = config('MONGODB_HOST', cast=str)
MONGODB_PORT = config('MONGODB_PORT', cast=int)
MONGODB_NAME = config('MONGODB_NAME', cast=str)

# Initialize the MongoDB client and database
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

def connect_to_mongodb(app, testing: bool = False):
    global client, db
    if testing:
        client = AsyncMongoMockClient()
    else:
        client = AsyncIOMotorClient(MONGODB_HOST, MONGODB_PORT)
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
        
async def seed_mongodb(mongodb: AsyncIOMotorClient, data: dict, clean: bool = True):
    counter = 0
    for key in data:
        if clean:
            await mongodb[key].drop()
        response = await mongodb[key].insert_many(jsonable_encoder(data[key]))
        counter += len(response.inserted_ids)
    
    return f"{counter} entries created"
