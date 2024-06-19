from pydantic import BaseModel, EmailStr,validator
from typing import List, Optional,Union,Any
import uuid
from datetime import datetime
import re

class UserCreate(BaseModel):
    name: str
    lastName: str
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, password, values):
        errors = []
        name = values.get('name', '').lower()
        last_name = values.get('lastName', '').lower()

        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one number')
        if not re.search(r'[\W_]', password):
            errors.append('Password must contain at least one special character')
        if name in password.lower() or last_name in password.lower():
            errors.append('Password cannot contain your first or last name')

        if errors:
            raise ValueError(' , '.join(errors))
        
        return password


class DefaultResponse(BaseModel):
    success: bool
    responseBody: Optional[Union[Any, str]]
    responseCode: str
    message: str
    currentTime: datetime



class User(BaseModel):
    id: uuid.UUID
    name: str
    lastName: str
    email: EmailStr
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True


class MessageCreate(BaseModel):
    content: str
    conversationId: uuid.UUID

class Message(BaseModel):
    id: uuid.UUID
    userId: uuid.UUID
    conversationId: uuid.UUID
    content: str
    createdAt: datetime
    updatedAt: datetime

class MessageIn(BaseModel):
    content: str
    userId: uuid.UUID
    conversationId: uuid.UUID

class TokenData(BaseModel):
    user_id: Optional[str] = None
