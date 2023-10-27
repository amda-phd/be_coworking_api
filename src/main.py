from fastapi import FastAPI, HTTPException, Response, status

from .db import connect_to_mongodb, close_mongodb_connection, ping_health
from .routers.rooms import router as rooms_router

app = FastAPI(
    title = "Coworking API",
    description = "The backend of meeting space booking app"
)

@app.on_event("startup")
async def on_startup():
    app.mongodb = await connect_to_mongodb()

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongodb_connection()

@app.get(
    "/health",
    status_code = 204,
    description = "Check the server's and MongoDB connection integrity",
    responses = {
        204: { "description": "Server and database reachable" },
        500: { "description": "Server unreachable" },
        503: { "description": "Database unreachable" }
    })
async def health():
    if (await ping_health()):
        return Response(status_code = status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=503, detail="MongoDB unavailable")

app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
