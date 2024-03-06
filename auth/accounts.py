import os
import secrets
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter

from database import get_async_session
from models.models import Users, Role
from .utils import generate_token, verify_token, algorithm
from .schemes import User, UserOutDB, UserInDB, UserLogin, UserOutDBScheme
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.exc import NoResultFound
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

register_router = APIRouter()


@register_router.post('/register')
async def register(user: User, session: AsyncSession = Depends(get_async_session)):
    # Check if passwords match
    if user.password1 != user.password2:
        raise HTTPException(status_code=400, detail="Passwords don't match")

    # Check if username already exists
    try:
        user_name = select(Users).where(Users.username == user.username)
        user_name_result = await session.execute(user_name)
        user_ = user_name_result.scalar()
        if user_:
            raise HTTPException(status_code=400, detail="Username already exists")
    except NoResultFound:
        pass

    # Hash the password
    password = pwd_context.hash(user.password1)
    # Create a UserInDB instance with hashed password
    user_in_db = UserInDB(**dict(user), password=password)

    # Convert UserInDB instance to dictionary
    user_in_db_dict = user_in_db.dict()
    # Insert user_in_db_dict into the database
    query = insert(Users).values(user_in_db_dict)
    await session.execute(query)
    await session.commit()

    # Create a UserOutDB instance for the response
    user_info = UserOutDB(**dict(user))
    return user_info


@register_router.post('/login')
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(Users).where(Users.username == user.username)
    user_data = await session.execute(query)
    try:
        user_data = user_data.scalar()
    except NoResultFound:
        raise HTTPException(status_code=400, detail="User not found")
    if pwd_context.verify(user.password, user_data.password):
        token = generate_token(user_data.id)
        return token
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")


@register_router.post('/refresh-token')
async def refresh_token(refresh_token: str):
    try:
        secret_key = os.getenv("SECRET")
        payload = jwt.decode(refresh_token, secret_key, algorithms=algorithm)
        jti_access = str(secrets.token_urlsafe(32))
        data_access_token = {
            'token_type': 'access',
            'exp': datetime.utcnow() + timedelta(hours=3),
            'user_id': payload.get('user_id'),
            'jti': jti_access
        }
        access_token = jwt.encode(data_access_token, secret_key, algorithm)
        return {
            'access_token': access_token
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid Token")


@register_router.get('/user-info', response_model=UserOutDBScheme) #Get user information
async def user_info(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = token.get('user_id')
    query = select(Users).where(Users.id == user_id)
    user__data = await session.execute(query)
    try:
        user_data = user__data.scalar()
        return user_data
    except NoResultFound:
        raise HTTPException(status_code=400, detail="User not found")


