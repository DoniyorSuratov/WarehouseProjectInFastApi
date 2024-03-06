from typing import List
from pydantic import BaseModel
from datetime import datetime


class WarehouseAddress(BaseModel):
    address: str
    name: str
    category_id: int

class WarehouseAddProductScheme(BaseModel):
    warehouse_id: int
    product_id: int
    amount: int
    price: float


class WarehouseGetProductScheme(BaseModel):
    warehouse_id: int
    product_id: int
    amount: int


class AboutWarehouseScheme(BaseModel):
    name: str
    longitude: float
    latitude: float
    category_id: int

class ExchangeProductScheme(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    amount: int
    product_id: int