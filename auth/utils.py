import secrets
from typing import List

import jwt
from datetime import datetime,timedelta
from jwt import PyJWTError
from config import SECRET
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
import os
from sqlalchemy.orm import selectinload
from admin.schemes import UserRoleScheme, ProductScheme
from models.models import Users, ShoppingCart, WarehouseExchangeHistory, ResourcesWarehouseData, WarehouseData
from shop.schemes import OrdersProductsScheme
from warehouse.schemes import MachineScheme, ShiftScheme, AboutWarehouseScheme, ResourcesWarehouseDataScheme, \
    ProductsScheme
from .schemes import UserOutDBScheme
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


async def get_user_info_by_id(user_id: int, session: AsyncSession) -> UserOutDBScheme:
    query = select(Users).options(selectinload(Users.machine), selectinload(Users.shift), selectinload(Users.role)).where(Users.id == user_id)
    user_data = await session.execute(query)
    user_data = user_data.scalar()

    if user_data is None:
        raise HTTPException(status_code=404, detail="User not found")
    machine_data = None
    if user_data.machine is not None:
        machine_data = MachineScheme(name=user_data.machine.name)

    return UserOutDBScheme(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        username=user_data.username,
        phone_number=user_data.phone_number,
        role=UserRoleScheme(role=user_data.role.role),
        shift=ShiftScheme(name=user_data.shift.name),
        machine=machine_data
    )

async def get_shopping_cart_by_order(user_id: int, order_id: int, session: AsyncSession) -> List[OrdersProductsScheme]:
    query = select(ShoppingCart).options(
        selectinload(ShoppingCart.product),
        selectinload(ShoppingCart.warehouse)
    ).where(
        ShoppingCart.user_id == user_id,
        ShoppingCart.order_id == order_id
    )
    result = await session.execute(query)
    shopping_cart_items = result.scalars().all()

    orders_products_list = []
    for item in shopping_cart_items:
        orders_products_list.append(
            OrdersProductsScheme(
                product=ProductScheme(
                    name=item.product.name,
                    category_id=item.product.category_id
                ),
                warehouse=AboutWarehouseScheme(
                    name=item.warehouse.name,
                    longitude=item.warehouse.longitude,
                    latitude=item.warehouse.latitude,
                    category_id=item.warehouse.category_id
                ),
                count=item.count,
                order_id=item.order_id
            )
        )
    return orders_products_list

async def get_resources_data(warehouse_id: int, session: AsyncSession) -> List[ResourcesWarehouseDataScheme]:
    query = select(ResourcesWarehouseData).options(selectinload(ResourcesWarehouseData.resource)).where(ResourcesWarehouseData.warehouse_id == warehouse_id)
    result = await session.execute(query)
    resources_data = result.scalars()
    resources_data_list=[]
    for item in resources_data:
        resources_data_list.append(
            ResourcesWarehouseDataScheme(
                resource=item.resource.name,
                resource_amount=item.resource_amount
            )

        )
    return resources_data_list


async def get_products_data(warehouse_id: int, session: AsyncSession) -> List[ProductsScheme]:
    query = select(WarehouseData).options(selectinload(WarehouseData.product)).where(WarehouseData.warehouse_id == warehouse_id)
    result = await session.execute(query)
    products_data = result.scalars()
    products_data_list=[]
    for item in products_data:
        products_data_list.append(
            ProductsScheme(
                product=item.product.name,
                price=item.price,
                amount=item.amount
            )
        )

    return products_data_list