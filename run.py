import uvicorn
from decouple import config

APP_PORT = config("PORT", cast=int)
APP_HOST = config("HOST", cast=str)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host = APP_HOST,
        port = APP_PORT
    )