from bson import ObjectId
from pydantic import BaseModel, Field

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
    _id: PyObjectId = Field(default_factory = PyObjectId)
    id: int = Field(gt = 0, default=0)

    class Config:
        json_encoders = { ObjectId: str }
 
    @staticmethod
    async def is_valid_id(id: int, collection) -> bool:
        return (await collection.find_one({ "id": id })) is None

    async def closest_valid_id(self, id: int, collection) -> int:
        if (await self.is_valid_id(id, collection)):
            return id
        return await self.closest_valid_id(id = id + 1, collection = collection)

    async def make_valid_id(self, collection) -> int:
        docs = await collection.count_documents({})
        return await self.closest_valid_id(id = docs + 1, collection=collection)

    async def add_id(self, collection):
        if self.id == 0:
            self.id = await self.make_valid_id(collection)
        elif not (await self.is_valid_id(self.id, collection)):
            raise ValueError("Invalid id")
        return self

        