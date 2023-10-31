from fastapi import APIRouter, Body, Request, status, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime


from ..db.models.rooms import RoomBase, RoomDB

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

@router.post("", description="Add a new available room")
async def create_room(request: Request, room: RoomBase = Body(...)) -> RoomDB:
    room = await room.add_id(collection=request.app.mongodb["rooms"])
    room = jsonable_encoder(room)
    new_room = await request.app.mongodb["rooms"].insert_one(room)
    created_room = await request.app.mongodb["rooms"].find_one({
        "_id": new_room.inserted_id
    })
    return created_room
    # return JSONResponse(status_code = status.HTTP_201_CREATED, content = created_room)

# TODO: Improve time validation
@router.get("/{id}/availability", description="Check availability for a room at a given time")
async def check_availability(id: int, request: Request, time):
    room = await request.app.mongodb["rooms"].find_one({ "id": id })
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Room with id {id} not found")
    bookings = await request.app.mongodb["bookings"].count_documents({
        "id_room": id,
        "start": { "$lte": time },
        "end": { "$gt": time }
    })
    return bookings == 0