from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError
import os
from backend.database.auth_db import AuthDB
from backend.utils.password_validation import validate_password

# JWT settings
# Change in production
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()
auth_db = AuthDB()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserCreate(BaseModel):
    username: str
    password: str


class User(BaseModel):
    user_id: int
    username: str
    registration_date: datetime


class UserActivity(BaseModel):
    action: str
    timestamp: datetime


@router.post("/signup")
async def signup(user: UserCreate):
    """Handle user registration"""
    success = auth_db.register_user(user.username, user.password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )
    return {"message": "User registered successfully"}


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> int:
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Handle user login and return access token"""
    user_id = auth_db.verify_user(form_data.username, form_data.password)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(user_id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(token: str = Depends(oauth2_scheme)):
    """Refresh access token"""
    try:
        user_id = verify_token(token)
        new_token = create_access_token({"sub": str(user_id)})
        return {"access_token": new_token, "token_type": "bearer"}
    except HTTPException:
        raise


@router.get("/user/activities")
async def get_user_activities(token: str = Depends(oauth2_scheme)):
    """Get user activities"""
    try:
        user_id = int(token)  # Convert token back to user_id
        activities = auth_db.get_user_activities(user_id)
        return {
            "activities": [
                {"action": action, "timestamp": timestamp}
                for action, timestamp in activities
            ]
        }
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )
