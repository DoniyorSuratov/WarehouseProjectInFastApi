from typing import List

from pydantic import BaseModel
from datetime import datetime

from admin.schemes import ProductScheme
from auth.schemes import UserOutDBScheme
from warehouse.schemes import WarehouseAddress, AboutWarehouseScheme



class AllProductsScheme(BaseModel):
    name: str
    category: str


class ProductsScheme(BaseModel):
    product_id: int
    count: int
    hash: str
    warehouse_id: int


class PaymentScheme(BaseModel):
    order_id: int
    payment: float

class ConfirmScheme(BaseModel):
    order_id: int
    hash: str

class OrdersProductsScheme(BaseModel):
    product: ProductScheme
    warehouse: AboutWarehouseScheme
    count: int
    order_id: int

class OrderScheme(BaseModel):
    user: UserOutDBScheme
    cart: List[OrdersProductsScheme]
    total_debt: float
    paid: float
    hash: str



