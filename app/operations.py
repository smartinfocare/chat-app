from sqlalchemy.orm import Session
from app import model, schemas
from app.redis import redis
import logging
from fastapi import HTTPException
from redis.exceptions import ConnectionError
import json

from typing import List
import uuid
from datetime import datetime
import bcrypt
logger = logging.getLogger(__name__)

async def get_user_by_email(db: Session, email: str):
    return db.query(model.User).filter(model.User.email == email).first()

async def get_user_by_id(db: Session, user_id: str):
    return db.query(model.User).filter(model.User.id == user_id).first()



async def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    db_user = model.User(name=user.name, lastName=user.lastName, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

async def add_message(conversation_id: uuid.UUID, message: dict, db: Session):
    try:
        content = message.get("content")
        userId = message.get("userId")
        if content is None or userId is None:
            raise ValueError("Message content or user_id is missing")

        user = db.query(model.User).filter(model.User.id == userId).first()
        if not user:
            raise ValueError("Invalid userId")

        message_id = uuid.uuid4()
        created_at = datetime.utcnow()
        updated_at = created_at
        message_data = json.dumps({
            "id": str(message_id),
            "content": content,
            "userId": str(userId),
            "conversationId": str(conversation_id),
            "createdAt": created_at.isoformat(),
            "updatedAt": updated_at.isoformat()
        })
        await redis.rpush(f"conversation:{str(conversation_id)}:messages", message_data)
        logger.debug("Message added to Redis")

        return schemas.Message(
            id=message_id,
            content=content,
            userId=userId,
            conversationId=conversation_id,
            createdAt=created_at,
            updatedAt=updated_at
        )
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(status_code=500, detail="Redis connection error")
    except ValueError as e:
        logger.error(f"Invalid message data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

async def get_messages(conversation_id: uuid.UUID) -> List[schemas.Message]:
    try:
        raw_messages = await redis.lrange(f"conversation:{str(conversation_id)}:messages", 0, -1)
        logger.debug(f"Messages retrieved from Redis: {raw_messages}")

        if not raw_messages:
            logger.info(f"No messages found for conversation_id: {conversation_id}")
            return []

        messages = []
        for raw_msg in raw_messages:
            try:
                msg_data = json.loads(raw_msg)
                messages.append(schemas.Message(
                    id=uuid.UUID(msg_data["id"]),
                    userId=uuid.UUID(msg_data["userId"]),
                    conversationId=conversation_id,
                    content=msg_data["content"],
                    createdAt=datetime.fromisoformat(msg_data["createdAt"]),
                    updatedAt=datetime.fromisoformat(msg_data["updatedAt"])
                ))
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding message from Redis: {e}")
                continue  # Skip invalid messages

        return messages
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(status_code=500, detail="Redis connection error")
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving messages")