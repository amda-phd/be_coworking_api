from fastapi import APIRouter, Request
from typing import Optional, List

from ..db import run_aggregation

router = APIRouter()

@router.get("/client_bookings", description="Get the number of bookings per client")
async def bookings_by_client(
    request: Request,
    id_client: Optional[int] = None,
    sort: Optional[str] = None
):
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