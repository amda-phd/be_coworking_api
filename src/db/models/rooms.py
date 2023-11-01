from ..models import MongoBaseModel
from pydantic import Field, constr, validator
from datetime import time

regex_time = r'^[0-1][0-9]:[0-5][0-9]|2[0-3]:[0-5][0-9]$'

class RoomDB(MongoBaseModel):
    capacity: int = Field(gt = 0)
    opening: constr(regex=regex_time)
    closing: constr(regex=regex_time)

class RoomBase(RoomDB):
    @validator('opening', 'closing')
    def validate_hours(cls, v):
        # Convert string to time object for comparison
        hours, minutes = map(int, v.split(':'))
        v_time = time(hours, minutes)

        # Check if time is between 0:00 and 23:59
        if not (time(0, 0) <= v_time <= time(23, 59)):
            raise ValueError('Time must be between 0:00 and 23:59')
        
        return v

    @validator('closing')
    def validate_closing(cls, v, values, **kwargs):
        if 'opening' in values:
            opening_time = time(*map(int, values['opening'].split(':')))
            closing_time = time(*map(int, v.split(':')))

            # Check if closing takes place after opening
            if closing_time <= opening_time:
                raise ValueError('Closing time must be after opening time')

        return v