from fastapi import APIRouter, HTTPException, Request, status
from typing import Optional
from datetime import datetime
from math import floor
import arrow
import re

from ..db import run_aggregation

regex_date = r'^\d{4}-\d{2}-\d{2}$'

router = APIRouter()

@router.get(
    "/client_bookings",
    description="Get the number of bookings per client. If no id_client is provided, the report for all the clients will be offered.",
    tags=["clients", "bookings"],
    responses = {
        404: { "description": "The requested id_client (if provided) cannot be found" }
    }
)
async def bookings_by_client(
    request: Request,
    id_client: Optional[int] = None,
    sort: Optional[str] = None
):
    if id_client is not None and (await request.app.mongodb["clients"].count_documents({ "id": id_client })) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id_client} not found")
    
    pipeline = [
        {
            "$group": {
                "_id": "$id_client",
                "total_bookings": { "$sum": 1 }
            }
        },
        {
            "$project": {
                "id_client": "$_id",
                "_id": 0,
                "total_bookings": 1
            }
        }
    ]
    if id_client:
        pipeline.append({
            "$match": {"id_client": id_client}
        })
    if sort:
        sorter = 1
        if sort == "DESC":
            sorter = -1
        pipeline.append({
            "$sort": { "total_bookings": sorter }
        })

    result = await run_aggregation(request.app.mongodb["bookings"], pipeline)
    return result

@router.get(
    "/room_usage",
    description="For a given time period, get the ratio of room usage. If no id_room is provided, the report for all the rooms will be offered.",
    tags=["rooms", "bookings"],
    responses = {
        404: { "description": "The requested id_room (if provided) cannot be found" }
    }
)
async def room_usage_by_period(
    request: Request,
    id_room: Optional[int] = None,
    from_day: str = None,
    to_day: str = None
):
    regex = re.compile(regex_date)
    if not regex.match(from_day) or not regex.match(to_day):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable time. Remember to use ZULU format")
    
    days = (arrow.get(to_day, "YYYY-MM-DD") - arrow.get(from_day, "YYYY-MM-DD")).days
    if days < 1:
        raise HTTPException(status_code=422, detail="to_day has to happen AFTER from_day")
    
    if id_room is not None and (await request.app.mongodb["rooms"].count_documents({ "id": id_room })) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with id {id_room} not found")

    milliseconds_in_minute = 60000
    from_datetime = datetime.strptime(from_day, '%Y-%m-%d')
    to_datetime = datetime.strptime(to_day, '%Y-%m-%d')
    
    opening_minutes_pipeline = [
        {
            "$addFields": {
                "openingTime": {
                    "$dateFromString": {
                        "dateString": {
                            "$concat": [from_day, "T", "$opening", "Z"]
                        },
                        "format": "%Y-%m-%dT%H:%MZ"
                    }
                },
                "closingTime": {
                    "$dateFromString": {
                        "dateString": {
                            "$concat": [from_day, "T", "$closing", "Z"]
                        },
                        "format": "%Y-%m-%dT%H:%MZ"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": "$id",
                "id_room": "$id",
                "opening_minutes_per_day": {
                    "$divide": [
                        {
                            "$subtract": ["$closingTime", "$openingTime"]
                        },
                        milliseconds_in_minute
                    ]
                }
            }
        },
        {
            "$sort": { "$id": 1 }
        }
    ]
    used_minutes_pipeline = [
        {
            "$addFields": {
                "start": {
                    "$dateFromString": {
                        "dateString": "$start"
                    }
                },
                "end": {
                    "$dateFromString": {
                        "dateString": "$end"
                    }
                }
            }
        },
        {
            "$match": {
                "start": { "$gte": from_datetime },
                "end": { "$lt": to_datetime }
            }
        },
        {
            "$addFields": {
                "minutes": {
                    "$divide":
                    [
                        {"$subtract": ["$end", "$start"]},
                        milliseconds_in_minute
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$id_room",
                "total_minutes": {"$sum": "$minutes"}
            }
        }
    ]
    if id_room:
        opening_minutes_pipeline.insert(0, {
            "$match": {"id": id_room}
        })
        used_minutes_pipeline.insert(0, {
            "$match": {"id_room": id_room}
        })
    
    opening_minutes = await run_aggregation(request.app.mongodb["rooms"], opening_minutes_pipeline)
    used_minutes = await run_aggregation(request.app.mongodb["bookings"], used_minutes_pipeline)

    result = []
    for room in opening_minutes:
        for booking in used_minutes:
            if room["_id"] == booking["_id"]:
                room["booked_minutes"] = booking["total_minutes"]
                room["opened_minutes"] = days * room["opening_minutes_per_day"]
                room["use_percentage"] = floor(1000 * room["booked_minutes"] / room["opened_minutes"]) / 10
                result.append(room)

    return result