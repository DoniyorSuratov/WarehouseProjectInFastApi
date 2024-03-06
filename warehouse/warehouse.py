import secrets
from typing import List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
import requests
from sqlalchemy import select, insert, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from auth.utils import verify_token
from database import get_async_session
from models.models import Warehouse, WarehouseCategory, WarehouseData, Products
from warehouse.schemes import WarehouseAddress, WarehouseAddProductScheme, WarehouseGetProductScheme, \
    AboutWarehouseScheme, ExchangeProductScheme

warehouse_router = APIRouter()

@warehouse_router.post('/create-warehouse')
async def create_warehouse(
        data_req: WarehouseAddress,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):

    response = requests.get("https://nominatim.openstreetmap.org/search", params={"q": data_req.address, "format": "json"})
    data = response.json()
    if data:
        # Extract the latitude and longitude from the response
        lat = data[0]["lat"]
        lon = data[0]["lon"]


        query = insert(Warehouse).values(name=data_req.name, latitude=float(lat), longitude=float(lon), category_id=data_req.category_id)
        await session.execute(query)
        await session.commit()
        return {"message": "Warehouse created successfully"}
    else:
        return {"message": "Geocoding data not found"}


@warehouse_router.post('/add-product')
async def add_product(
        data: WarehouseAddProductScheme,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = insert(WarehouseData).values(warehouse_id=data.warehouse_id, product_id=data.product_id, amount=data.amount, price=data.price)
        await session.execute(query)
        await session.commit()
        return {"status": "success", "message": "Product added successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@warehouse_router.get('/warehouse-info', response_model=List[WarehouseGetProductScheme])
async def warehouse_info(
        warehouse_id:int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(WarehouseData).where(WarehouseData.warehouse_id == warehouse_id)
        data = await session.execute(query)
        data = data.scalars()
        return data
    except:
        raise HTTPException(status_code=500, detail="Warehouse is empty")


@warehouse_router.post('/exchange-product')
async def exchange_product(
        data: ExchangeProductScheme,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    query1 = select(WarehouseData.amount).where(WarehouseData.warehouse_id == data.from_warehouse_id and WarehouseData.product_id == data.product_id)
    query_data = await session.execute(query1)
    query1_data = query_data.scalar()
    print(query1_data)

    query2 = select(WarehouseData.amount).where(
        WarehouseData.warehouse_id == data.to_warehouse_id and WarehouseData.product_id == data.product_id)
    query_data = await session.execute(query2)
    query2_data = query_data.scalar()
    print(query2_data)

    if query1_data < data.amount:
        raise HTTPException(status_code=500, detail=f"Not enought products for {data.product_id}")
    new_amount = query1_data - data.amount
    new_amount_add = query2_data + data.amount

    query = update(WarehouseData).where(WarehouseData.warehouse_id == data.from_warehouse_id and WarehouseData.product_id == data.product_id).values(amount=new_amount, warehouse_id=data.to_warehouse_id )
    await session.execute(query)

    query = update(WarehouseData).where(
        WarehouseData.warehouse_id == data.to_warehouse_id and WarehouseData.product_id == data.product_id).values(
        amount=new_amount_add, warehouse_id=data.to_warehouse_id)
    await session.execute(query)

    await session.commit()