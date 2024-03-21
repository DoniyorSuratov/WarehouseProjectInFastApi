from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from sqlalchemy import TIMESTAMP




class WarehouseAddress(BaseModel):
    address: str
    name: str
    category_id: int

class WarehouseAddProductScheme(BaseModel):
    warehouse_id: int
    product_id: int
    amount: int
    price: float


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


class ExchangeProductHistoryScheme(BaseModel):
    from_warehouse: int
    to_warehouse: int
    product_id: int


class DeleteProductWarehouseScheme(BaseModel):
    warehouse_id: int
    product_id: int
    reason: str


class GetProductScheme(BaseModel):
    warehouse_id: int
    product_id: int
    amount: int
    price: float


class ShiftScheme(BaseModel):
    name: str


class MachineScheme(BaseModel):
    name: str

class ProductsScheme(BaseModel):
    product: str
    price: float
    amount: int


class ResourcesWarehouseScheme(BaseModel):
    resource_amount: float
    resource: str
    paint: str


class ResourcesWarehouseDataScheme(BaseModel):
    resource: str
    resource_amount: float


class WarehouseInfoScheme(BaseModel):
    warehouse: AboutWarehouseScheme
    product: Optional[List[ProductsScheme]]
    resources: Optional[List[ResourcesWarehouseDataScheme]]



class WarehouseExchangeHistoryScheme(BaseModel):
    product: ProductsScheme
    from_warehouse_id: int
    to_warehouse_id: int
    last_update: Optional[datetime] = None


class ResourcesAddWarehouseScheme(BaseModel):
    warehouse_id: int
    resource_amount: float
    resource_id: int

class ExchangeResourcesScheme(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    resource_amount: int
    resource_id: int


class AddResieptScheme(BaseModel):
    reciept_id: int
    product_id: int
    resource_id: int
    resource_amount: float

class GetRecieptsScheme(BaseModel):
    resource: str
    resource_amount: float


class GetResourcesScheme(BaseModel):
    warehouse_id: int
    reciept_id: int
    amount: int