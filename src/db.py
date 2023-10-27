from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from decouple import config
from bson import ObjectId
from pydantic import BaseModel, Field

MONGODB_URL = config('MONGODB_URL', cast=str)
MONGODB_NAME = config('MONGODB_NAME', cast=str)

# Initialize the MongoDB client and database
client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type = "string")

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory = PyObjectId, alias = "_id")

    class Config:
        json_encoders = { ObjectId: str }

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