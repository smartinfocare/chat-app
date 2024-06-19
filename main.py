from fastapi import FastAPI,Request
from app.api.routes import auth, chat
from app.webSocket import router as websocket_router
from app.database import database, engine
from app.model import Base
import logging

app = FastAPI()

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='passlib.handlers.bcrypt')


Base.metadata.create_all(bind=engine)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(websocket_router, tags=["websockets"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Middleware to log requests and responses
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
