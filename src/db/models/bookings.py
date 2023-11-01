from ..models import PyObjectId, MongoBaseModel
from pydantic import Field
from datetime import datetime

regex_datetime = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$'

class BookingBase(MongoBaseModel):
    id_room: PyObjectId = Field(...)
    id_client: PyObjectId = Field(...)
    start: datetime = Field(...)
    end: datetime = Field(...)