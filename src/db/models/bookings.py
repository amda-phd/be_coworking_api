from ..models import PyObjectId, MongoBaseModel
from pydantic import Field
from datetime import datetime

class BookingBase(MongoBaseModel):
    id_room: PyObjectId = Field(...)
    id_client: PyObjectId = Field(...)
    start: datetime = Field(...)
    end: datetime = Field(...)