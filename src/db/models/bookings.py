from ..models import MongoBaseModel
from pydantic import Field, validator, constr
from datetime import datetime

regex_datetime = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$'

class BookingDB(MongoBaseModel):
    id_room: int = Field(gt = 0)
    id_client: int = Field(gt = 0)
    start: constr(regex=regex_datetime)
    end: constr(regex=regex_datetime)

class BookingBase(BookingDB):
    @validator('start', 'end')
    def validate_datetime(cls, v):
        if datetime.strptime(v, '%Y-%m-%dT%H:%MZ') < datetime.utcnow():
            raise ValueError("You cannot make bookings in the past")
        
        return v
    
    @validator('end')
    def validate_end(cls, v, values, **kwargs):
        start_time = datetime.strptime(values['start'], '%Y-%m-%dT%H:%MZ')
        end_time = datetime.strptime(v, '%Y-%m-%dT%H:%MZ')
        if end_time < start_time:
            raise ValueError("End time cannot be before start time")
        
        return v