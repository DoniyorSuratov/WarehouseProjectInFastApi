import secrets
from typing import List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
import requests
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

from auth.utils import verify_token
from database import get_async_session
from models.models import Warehouse, WarehouseCategory, WarehouseData, Products, WarehouseExchangeHistory, \
    DeletedProductsWarehouse
from .schemes import WarehouseAddress, WarehouseAddProductScheme, WarehouseGetProductScheme, \
    ExchangeProductScheme, ExchangeProductHistoryScheme, DeleteProductWarehouseScheme, GetProductScheme
from .utils import is_admin

warehouse_router = APIRouter()

@warehouse_router.post('/create-warehouse')
async def create_warehouse(
        data_req: WarehouseAddress,
        token: dict = Depends(is_admin),
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
        token: dict = Depends(is_admin),
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
        token: dict = Depends(is_admin),
        session: AsyncSession = Depends(get_async_session)
):

    # Check if the product exists in the from_warehouse_id
    query1 = select(WarehouseData).where(
        and_(WarehouseData.warehouse_id == data.from_warehouse_id,
             WarehouseData.product_id == data.product_id)
    )
    query_data = await session.execute(query1)
    query1_data = query_data.scalar()

    if not query1_data:
        raise HTTPException(status_code=404, detail=f"Product {data.product_id} not found in warehouse {data.from_warehouse_id}")

    # Check if the product exists in the to_warehouse_id
    query2 = select(WarehouseData.amount).where(
        and_(WarehouseData.warehouse_id == data.to_warehouse_id,
             WarehouseData.product_id == data.product_id)
    )
    query_data = await session.execute(query2)
    query2_data = query_data.scalar()

    if query2_data is None:
        # Product doesn't exist in to_warehouse_id, insert new product
        query = insert(WarehouseData).values(
            amount=data.amount,
            warehouse_id=data.to_warehouse_id,
            product_id=data.product_id,
            price=query1_data.price
        )
        await session.execute(query)
    else:
        # Product exists in to_warehouse_id, update amounts
        new_amount_from = query1_data.amount - data.amount
        new_amount_to = query2_data + data.amount

        query = update(WarehouseData).where(
            and_(WarehouseData.warehouse_id == data.from_warehouse_id,
                 WarehouseData.product_id == data.product_id)
        ).values(amount=new_amount_from)
        await session.execute(query)

        query = update(WarehouseData).where(
            and_(WarehouseData.warehouse_id == data.to_warehouse_id,
                 WarehouseData.product_id == data.product_id)
        ).values(amount=new_amount_to)
        await session.execute(query)

    query3 = insert(WarehouseExchangeHistory).values(
        product_id=data.product_id,
        from_warehouse=data.from_warehouse_id,
        to_warehouse=data.to_warehouse_id
    )
    await session.execute(query3)
    await session.commit()

    return {"message": "Exchange successful"}


@warehouse_router.get('/exchanges', response_model=List[ExchangeProductHistoryScheme])
async def get_exchanges(
        warehouse_id: int,
        token: dict = Depends(is_admin),
        session: Session = Depends(get_async_session)
):
    try:
        query = select(WarehouseExchangeHistory).where(WarehouseExchangeHistory.from_warehouse == warehouse_id)
        result = await session.execute(query)
        result_ = result.scalars()
        return result_
    except:
        return {"message": "There is any changes"}


@warehouse_router.delete('/dpw')
async def delete_dpw(
        data: DeleteProductWarehouseScheme,
        token: dict  = Depends(is_admin),
        session: Session = Depends(get_async_session)
):
    user_id = token.get('user_id')
    query = select(WarehouseData).where(and_(WarehouseData.warehouse_id == data.warehouse_id,
                                             WarehouseData.product_id == data.product_id))
    result = await session.execute(query)
    result = result.scalar()

    if not result:
        raise HTTPException (status_code=400, detail="The product or warehouse does not exist")

    await session.execute(delete(WarehouseData).where(and_(WarehouseData.warehouse_id == data.warehouse_id,
                                                           WarehouseData.product_id == data.product_id)))
    await session.execute(insert(DeletedProductsWarehouse).values([
        {'warehouse_id': data.warehouse_id, 'reason': data.reason, 'product_id': data.product_id, 'user_id': user_id}
    ]))
    await session.commit()


@warehouse_router.get('/search-product', response_model=List[GetProductScheme])
async def search_product(
        product_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(WarehouseData).where(WarehouseData.product_id == product_id)
        result = await session.execute(query)
        result = result.scalars()
        return result
    except:
        raise HTTPException(status_code=400, detail="The product does not exist")
