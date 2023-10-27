from ..models import MongoBaseModel
from pydantic import Field

class RoomBase(MongoBaseModel):
    capacity: int = Field(gt = 0)
    opening: int = Field(ge = 0)
    closing: int = Field(le = 2400)