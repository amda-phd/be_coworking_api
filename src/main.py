from fastapi import FastAPI, HTTPException, Response, status, Request

from .db import connect_to_mongodb, close_mongodb_connection, ping_mongodb
from .routers.rooms import router as rooms_router

app = FastAPI(
    title = "Coworking API",
    description = "The backend of meeting space booking app"
)

@app.on_event("startup")
def on_startup():
    connect_to_mongodb(app)

@app.on_event("shutdown")
def on_shutdown():
    close_mongodb_connection(app)

@app.get(
    "/health",
    status_code = 204,
    description = "Check the server's and MongoDB connection integrity",
    responses = {
        204: { "description": "Server and database reachable" },
        500: { "description": "Server unreachable" },
        503: { "description": "Database unreachable" }
    })
async def health(request: Request):
    try:
        await ping_mongodb(request.app.mongodb)
        return Response(status_code = status.HTTP_204_NO_CONTENT)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=503, detail="MongoDB unavailable")

app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
