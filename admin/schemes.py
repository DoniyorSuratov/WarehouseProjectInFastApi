from pydantic import BaseModel
from datetime import datetime

class CategoryAddScheme(BaseModel):
    name: str

class UserRoleScheme(BaseModel):
    role: str

class ProductScheme(BaseModel):
    name: str
    amount: int
    category_id: int