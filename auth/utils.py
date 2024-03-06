import secrets
import jwt
from datetime import datetime,timedelta
from jwt import PyJWTError
from config import SECRET
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import os

secret_key = os.environ.get('SECRET')
algorithm = 'HS256'
security = HTTPBearer()
def generate_token(user_id : int):
    jti_access = secrets.token_urlsafe(32)
    jti_refresh = secrets.token_urlsafe(32)

    payload_access = {
        'type': 'access',
        'exp': datetime.utcnow()+timedelta(hours=1),
        'user_id': user_id,
        'jti': jti_access
    }

    payload_refresh = {
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=1),
        'user_id': user_id,
        'jti': jti_refresh
    }

    access_token = jwt.encode(payload_access, SECRET, algorithm=algorithm)
    refresh_token = jwt.encode(payload_refresh, SECRET, algorithm=algorithm)
    return {
        'refresh': refresh_token,
        'access': access_token
    }

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail='Token has expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail='Token is invalid')

def create_reset_pasword_token(email: str):
    data = {"sub": email, "exp": datetime.utcnow() + timedelta(minutes=10)}
    token = jwt.encode(data, SECRET, algorithm=algorithm)
    return token

def decode_reset_password_token(token: str):
    try:
        payload = jwt.decode(token, secret_key,
                   algorithms=algorithm)
        email: str = payload.get("sub")
        return email
    except PyJWTError:
        return None