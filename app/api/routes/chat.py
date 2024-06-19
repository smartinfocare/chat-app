from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app import schemas, operations
from app.database import get_db
from typing import List
import uuid
from datetime import datetime
from .auth import get_current_user

router = APIRouter()

@router.post("/messages", response_model=schemas.DefaultResponse)
async def create_message(message: schemas.MessageIn, token: str = Header(None), db: Session = Depends(get_db)):
    if not token:
        return schemas.DefaultResponse(
            success=False,
            responseBody={},
            responseCode="Fail",
            message="Authorization header missing",
            currentTime=datetime.utcnow()
        )
    
    token1 = token.split()[-1]
    if not token1:
        return schemas.DefaultResponse(
            success=False,
            responseBody=None,
            responseCode="Fail",
            message="Bearer token missing",
            currentTime=datetime.utcnow()
        )
    
    current_user = await get_current_user(token1, db)
    created_message = await operations.add_message(message.conversationId, message.dict(), db)
    return schemas.DefaultResponse(
        success=True,
        response_body=created_message,
        response_code="Success",
        message="Message created successfully",
        currentTime=datetime.utcnow()
    )

@router.get("/messages/{conversationId}", response_model=schemas.DefaultResponse)
async def get_messages(conversationId: uuid.UUID, token: str = Header(None), db: Session = Depends(get_db)):
    if not token:
        return schemas.DefaultResponse(
            success=False,
            responseBody=None,
            responseCode="Fail",
            message="Authorization header missing",
            currentTime=datetime.utcnow()
        )
    
    verify = token.split()[-1]
    if not verify:
        return schemas.DefaultResponse(
            success=False,
            responseBody=None,
            responseCode="Fail",
            message="Bearer token missing",
            currentTime=datetime.utcnow()
        )
    
    current_user = await get_current_user(verify, db)
    messages = await operations.get_messages(conversationId)
    return schemas.DefaultResponse(
        success=True,
        responseBody=messages,
        responseCode="Success",
        message="Messages fetched successfully",
        currentTime=datetime.utcnow()
    )
