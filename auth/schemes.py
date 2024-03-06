from pydantic import BaseModel
from datetime import datetime


class User(BaseModel): #get from front-end
    first_name: str
    last_name: str
    password1: str
    password2: str
    username: str
    phone_number: str
    role_id: int


class UserInDB(BaseModel): #save to DB
    first_name: str
    username: str
    password: str
    last_name: str
    phone_number: str

class UserOutDB(BaseModel):
    first_name: str
    username: str
    last_name: str
    phone_number: str

class UserOutDBScheme(BaseModel):
    id: int
    first_name: str
    username: str


class UserLogin(BaseModel):
    username: str
    password: str
