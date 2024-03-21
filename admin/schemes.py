from pydantic import BaseModel
from datetime import datetime

class CategoryAddScheme(BaseModel):
    name: str

class UserRoleScheme(BaseModel):
    role: str

class ProductScheme(BaseModel):
    name: str
    category_id: int


class UserMachineScheme(BaseModel):
    username: str
    machine_id: int

class AddShiftScheme(BaseModel):
    username: str
    shift_id: int