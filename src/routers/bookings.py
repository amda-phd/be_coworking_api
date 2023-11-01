from fastapi import APIRouter, Body, Request, status, HTTPException
from typing import Optional, List

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