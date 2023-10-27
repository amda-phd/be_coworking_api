from ..models import MongoBaseModel
from pydantic import Field

class ClientBase(MongoBaseModel):
    name: str = Field(..., min_length = 3)