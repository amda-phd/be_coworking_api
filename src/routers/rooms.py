from fastapi import APIRouter, Body, Request, status, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import List
import re

from ..db.models.bookings import regex_datetime
from ..db.models.rooms import RoomBase, RoomDB
from ..db import run_aggregation

router = APIRouter()

@router.get("", description="List rooms with basic pagination")
async def list_rooms(
    request: Request,
    lim: int = 10,
    page: int = 1
) -> List[RoomDB]:
    skip = (page - 1)*lim
    full_query = request.app.mongodb["rooms"].find({}).skip(skip).limit(lim)
    results = [RoomDB(**raw_room) async for raw_room in full_query]
    return results

@router.post(
    "",
    description="Add a new available room",
    status_code=201,
    responses = {
        201: { "description": "Room processed correctly and recorded in the database" },
    }
)
async def create_room(request: Request, room: RoomBase = Body(...)) -> RoomDB:
    room = await room.add_id(collection=request.app.mongodb["rooms"])
    room = jsonable_encoder(room)
    new_room = await request.app.mongodb["rooms"].insert_one(room)
    created_room = await request.app.mongodb["rooms"].find_one({
        "_id": new_room.inserted_id
    }, { "_id": 0})
    return JSONResponse(status_code = status.HTTP_201_CREATED, content = created_room)

# TODO: Improve time validation using arrow and add "human-friendly" times (like now, today...)
@router.get(
    "/{id}/availability",
    description="Check availability for a room at a given time",
    responses = {
        200: { "description": "The parameters have been processed correctly and the answer has been obtained" },
        404: { "description": "The requested room doesn't exist in the database" }
    }
)
async def check_availability(id: int, request: Request, time: str) -> bool:
    regex = re.compile(regex_datetime)
    if not regex.match(time):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable time. Remember to use ZULU format")
    room = await request.app.mongodb["rooms"].find_one({ "id": id })
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with id {id} not found")
    bookings = await request.app.mongodb["bookings"].count_documents({
        "id_room": id,
        "start": { "$lte": time },
        "end": { "$gt": time }
    })
    return bookings == 0

@router.get(
    "/{id}/overlap",
    description="Find overlapping bookings for a given room",
    responses = {
        200: { "description": "The parameters have been processed correctly and the answer has been obtained" },
        404: { "description": "The requested room doesn't exist in the database" }
    }
)
async def check_overlaps(id: int, request: Request):
    room = await request.app.mongodb["rooms"].count_documents({ "id": id })
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with id {id} not found")
    
    pipeline = [
        {
            "$match": {"id_room": id}
        },
        {
            "$group": {
                "_id": "$id_room",
                "bookings": {
                    "$push": {
                        "id_client": "$id_client",
                        "start": "$start",
                        "end": "$end"
                    }
                }
            }
        },
        {
            "$project": {
                "room": "$_id",
                "overlapping_bookings": {
                    "$filter": {
                        "input": "$bookings",
                        "as": "booking",
                        "cond": {
                            "$anyElementTrue": {
                                "$map": {
                                    "input": "$bookings",
                                    "as": "otherBooking",
                                    "in": {
                                        "$and": [
                                            {"$ne": ["$$booking.id_client", "$$otherBooking.id_client"]},
                                            {"$lt": ["$$booking.start", "$$otherBooking.end"]},
                                            {"$gt": ["$$booking.end", "$$otherBooking.start"]}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "$match": {
                "overlapping_bookings": {"$ne": []}
            }
        }
    ]

    result = await run_aggregation(request.app.mongodb["bookings"], pipeline)
    return result