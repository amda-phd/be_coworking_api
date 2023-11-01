from datetime import datetime
from fastapi import APIRouter, Body, Request, status, HTTPException
from typing import Optional, List

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ..db.models.bookings import BookingBase, BookingDB

router = APIRouter()

@router.get("", description="List bookings with basic pagination and filtering by client and room")
async def list_bookings(
    request: Request,
    id_client: Optional[int] = None,
    id_room: Optional[int] = None,
    lim: int = 10,
    page: int = 1
):
    skip = (page - 1)*lim
    query = {}
    if id_client:
        query["id_client"] = id_client
    if id_room:
        query["id_room"] = id_room
    full_query = request.app.mongodb["bookings"].find(query).skip(skip).limit(lim)
    results = [BookingDB(**raw_booking) async for raw_booking in full_query]
    return results

@router.post("", description="Add a new booking for a room and client")
async def create_booking(request: Request, booking: BookingBase = Body(...)):
    # Check that the client exists
    if (await request.app.mongodb["clients"].count_documents({ "id": booking.id_client })) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {booking.id_client} not found")

    # Check that the room exists
    room = await request.app.mongodb["rooms"].find_one({ "id": booking.id_room })
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with id {booking.id_room} not found")
    
    # Check that the room will be opened
    opening = datetime.strptime(room["opening"], '%H:%M')
    start = datetime.strptime(booking.start, '%Y-%m-%dT%H:%MZ')
    opening = start.replace(hour=opening.hour, minute=opening.minute)
    closing = datetime.strptime(room["closing"], '%H:%M')
    end = datetime.strptime(booking.end, '%Y-%m-%dT%H:%MZ')
    closing = end.replace(hour=closing.hour, minute=closing.minute)
    if start < opening or start > closing or end > closing:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"We're sorry. The room with id {booking.id_room} won't be opened at the requested hours. Please, try a different schedule")

    # Check that the room is available at the requested time
    if (await request.app.mongodb["bookings"].count_documents({
        "id_room": booking.id_room,
        "$or": [
            { "$and": [
                { "start": { "$lte": booking.start } },
                { "end": { "$gt": booking.start } }
                ]
            },
            {
                "$and": [
                    { "start": { "$gt": booking.end } },
                    { "end": { "$lte": booking.end } }
                ]
            }
        ]
    })) != 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"We're sorry. The room with id {booking.id_room} is already booked at these hours. Please, try a different room or different schedule")
    
    booking = await booking.add_id(collection = request.app.mongodb["bookings"])
    booking = jsonable_encoder(booking)
    new_booking = await request.app.mongodb["bookings"].insert_one(booking)
    created_booking = await request.app.mongodb["bookings"].find_one({
        "_id": new_booking.inserted_id
    }, { "_id": 0})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_booking)