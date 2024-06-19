from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from app import schemas, operations
from app.database import get_db
from app.config import settings
import logging

router = APIRouter()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(username: str, password: str, db: Session):
    user = await operations.get_user_by_email(db, email=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def verify_password(plain_password, hashed_password):
    try:
        logging.info(f"Verifying password with hashed password: {hashed_password}")
        is_verified = pwd_context.verify(plain_password, hashed_password)
        logging.info(f"Password verification result: {is_verified}")
        return is_verified
    except Exception as e:
        logging.error(f"Error occurred during password verification: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/token", response_model=schemas.DefaultResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return schemas.DefaultResponse(
            success=False,
            responseBody=None,
            responseCode="Fail",
            message="Incorrect username or password",
            currentTime=datetime.utcnow()
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return schemas.DefaultResponse(
        success=True,
        responseBody={"accessToken": access_token, "tokenType": "bearer", "expiresIn": ACCESS_TOKEN_EXPIRE_MINUTES, "userId": user.id},
        responseCode="Success",
        message="Token created successfully",
        currentTime=datetime.utcnow()
    )

async def get_current_user(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = await operations.get_user_by_email(db, email=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

@router.post("/signup", response_model=schemas.DefaultResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = await operations.get_user_by_email(db, email=user.email)
    if db_user:
        return schemas.DefaultResponse(
            success=False,
            response_body=None,
            response_code="Fail",
            message="Email already registered",
            currentTime=datetime.utcnow()
        )
    
    try:
        schemas.UserCreate(**user.dict())
    except ValueError as e:
        print(e)
        return schemas.DefaultResponse(
            success=False,
            responseBody=None,
            responseCode="Fail",
            message=str(e),
            currentTime=datetime.utcnow()
        )

    created_user = await operations.create_user(db=db, user=schemas.UserCreate(**user.dict(), hashed_password=hashed_password))
    return schemas.DefaultResponse(
        success=True,
        response_body=created_user,
        response_code="Success",
        message="User created successfully",
        currentTime=datetime.utcnow()
    )
