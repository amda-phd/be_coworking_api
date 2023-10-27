from fastapi import FastAPI
from .db import connect_to_mongodb, close_mongodb_connection

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await connect_to_mongodb()

@app.on_event("shutdown")
async def on_shutdown():
    await close_mongodb_connection()

@app.get("/health")
async def health():
    return { "API": True }
