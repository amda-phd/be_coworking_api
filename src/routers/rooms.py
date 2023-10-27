from fastapi import APIRouter, Body, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import List, Optional

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
    room = jsonable_encoder(room)
    new_room = await request.app.mongodb["rooms"].insert_one(room)
    created_room = await request.app.mongodb["rooms"].find_one({
        "_id": new_room.inserted_id
    })
    return JSONResponse(status_code = status.HTTP_201_CREATED, content = created_room)