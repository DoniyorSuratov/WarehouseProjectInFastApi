from typing import List

from pydantic import BaseModel
from datetime import datetime

class AllProductsScheme(BaseModel):
    name: str
    category_id: int


class ProductsScheme(BaseModel):
    product_id: int
    count: int
    hash: str
    warehouse_id: int


class PaymentScheme(BaseModel):
    order_id: int
    payment: float

class ConfirmScheme(BaseModel):
    cart_id: int
    hash: str


