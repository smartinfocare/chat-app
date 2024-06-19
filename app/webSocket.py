from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.redis import redis

router = APIRouter()

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"conversation:{conversation_id}:channel")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        await pubsub.unsubscribe(f"conversation:{conversation_id}:channel")
