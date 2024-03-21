import secrets
from typing import List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
import requests
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.operators import and_

from admin.schemes import UserRoleScheme
from auth.schemes import UserOutDB, UserOutDBScheme
from auth.utils import verify_token, get_resources_data, get_products_data
from database import get_async_session
from models.models import Warehouse, WarehouseCategory, WarehouseData, Products, WarehouseExchangeHistory, \
    DeletedProductsWarehouse, Users, ResourcesWarehouseData, Reciept, RecieptForProducts

from .schemes import WarehouseAddress, WarehouseAddProductScheme, \
    ExchangeProductScheme, ExchangeProductHistoryScheme, DeleteProductWarehouseScheme, GetProductScheme, \
    ShiftScheme, WarehouseInfoScheme, AboutWarehouseScheme, ProductsScheme, WarehouseExchangeHistoryScheme, \
    MachineScheme, ResourcesAddWarehouseScheme, ExchangeResourcesScheme, AddResieptScheme, GetRecieptsScheme, \
    GetResourcesScheme
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


@warehouse_router.get('/warehouse-info', response_model=List[WarehouseInfoScheme])
async def warehouse_info(
        warehouse_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(WarehouseData).options(
            selectinload(WarehouseData.warehouse),
            selectinload(WarehouseData.product)
        ).where(WarehouseData.warehouse_id == warehouse_id)



        data = await session.execute(query)
        datas = data.scalars()

        warehouse_info = []

        for data_ in datas:
            resources_data = await get_resources_data(warehouse_id, session)
            product_data = await get_products_data(warehouse_id, session)
            warehouse_info.append(WarehouseInfoScheme(
                warehouse=AboutWarehouseScheme(
                    name=data_.warehouse.name,
                    longitude=data_.warehouse.longitude,
                    latitude=data_.warehouse.latitude,
                    category_id=data_.warehouse.category_id,
                ),
                product=product_data,
                resources=resources_data,
            ))
            break
        return warehouse_info
    except Exception as e:
        raise HTTPException(status_code=500, detail="Warehouse info not found")


@warehouse_router.get('/all-warehouse-info', response_model=List[WarehouseInfoScheme])
async def warehouse_info(
        # token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = select(WarehouseData).union(select(ResourcesWarehouseData)).options(
            selectinload(WarehouseData.warehouse),
            selectinload(WarehouseData.product)
        )

        data = await session.execute(query)
        datas = data.scalars()

        warehouse_info = []
        for data_ in datas:
            product_data = await get_products_data(data_.warehouse_id, session)
            resources_data = await get_resources_data(data_.warehouse_id, session)
            warehouse_info.append(WarehouseInfoScheme(
                warehouse=AboutWarehouseScheme(
                    name=data_.warehouse.name,
                    longitude=data_.warehouse.longitude,
                    latitude=data_.warehouse.latitude,
                    category_id=data_.warehouse.category_id,
                ),
                product=product_data,
                resources=resources_data,
            ))
        return warehouse_info
    except Exception as e:
        raise HTTPException(status_code=500, detail="Warehouse info not found")



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
    # Product exists in to_warehouse_id, update amounts
    new_amount_from = query1_data.amount - data.amount
    new_amount_to = query2_data + data.amount

    if query2_data is None:
        # Product doesn't exist in to_warehouse_id, insert new product
        query = insert(WarehouseData).values(
            amount=data.amount,
            warehouse_id=data.to_warehouse_id,
            product_id=data.product_id,
            price=query1_data.price
        )
        await session.execute(query)
        #update from_warehouse product_amount
        query = update(WarehouseData).where(
            and_(WarehouseData.warehouse_id == data.from_warehouse_id,
                 WarehouseData.product_id == data.product_id)
        ).values(amount=new_amount_from)
        await session.execute(query)


    else:

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


@warehouse_router.get('/exchanges', response_model=List[WarehouseExchangeHistoryScheme])
async def get_exchanges(
        warehouse_id: int,
        session: Session = Depends(get_async_session)
):
    try:
        query = select(WarehouseExchangeHistory).options(selectinload(WarehouseExchangeHistory.product)).where(WarehouseExchangeHistory.from_warehouse_id == warehouse_id)
        result = await session.execute(query)
        result_ = result.scalars()
        exchange_data = []

        for data in result_:
            print(data.warehouse.name)
            exchange_data.append(WarehouseExchangeHistoryScheme(
                product=ProductsScheme(
                    name=data.product.name,
                    category_id=data.product.category_id
                ),
                from_warehouse_id=data.from_warehouse_id,
                to_warehouse_id=data.to_warehouse_id,
                last_updated=data.last_update
            ))

        return exchange_data
    except Exception as e:
        print(f"Error: {e}")
        return []


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


@warehouse_router.get('/user-machine', response_model=List[UserOutDBScheme])
async def user_machine(
        machine_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(Users).options(selectinload(Users.machine), selectinload(Users.shift), selectinload(Users.role)).where(Users.machine_id == machine_id)
    result = await session.execute(query)
    users = result.scalars().all()
    users_warehouse_list = []
    for user in users:
        if user.role.role == 'worker':
            user_warehouse = UserOutDBScheme(
                first_name=user.first_name,
                username=user.username,
                last_name=user.last_name,
                phone_number=user.phone_number,
                role=UserRoleScheme(role=user.role.role),
                shift=ShiftScheme(name=user.shift.name),
                machine=MachineScheme(name=user.machine.name)
            )
            users_warehouse_list.append(user_warehouse)
        else:
            raise HTTPException(status_code=400, detail="This User has no machine or user does not exist")

    return users_warehouse_list



@warehouse_router.post('/add-resources')
async def add_paint_to_warehouse(
        data: ResourcesAddWarehouseScheme,
        session: Session = Depends(get_async_session)

):
    try:
        query = insert(ResourcesWarehouseData).values(**data.dict())
        await session.execute(query)
        await session.commit()
        return {"status": True, "message": "Resource added successfully"}
    except Exception as e:
        raise HTTPException( status_code=400, detail=f"{e}")


@warehouse_router.post('/exchange-resources')
async def exchange_product(
        data: ExchangeResourcesScheme,
        # token: dict = Depends(is_admin),
        session: AsyncSession = Depends(get_async_session)
):
    if data.resource_amount is not None:
        # Check if the resource exists in the from_warehouse_id
        query1 = select(ResourcesWarehouseData).where(
            and_(ResourcesWarehouseData.warehouse_id == data.from_warehouse_id,
                 ResourcesWarehouseData.resource_id == data.resource_id)
        )
        query_data = await session.execute(query1)
        query1_data = query_data.scalar()

        if not query1_data:
            raise HTTPException(status_code=404, detail=f"Resource {data.resource_id} not found in warehouse {data.from_warehouse_id}")

        # Check if the product exists in the to_warehouse_id
        query2 = select(ResourcesWarehouseData.resource_amount).where(
            and_(ResourcesWarehouseData.warehouse_id == data.to_warehouse_id,
                 ResourcesWarehouseData.resource_id == data.resource_id)
        )
        query_data = await session.execute(query2)
        query2_data = query_data.scalar()

        if query2_data is None:
            # Product doesn't exist in to_warehouse_id, insert new product
            query = insert(ResourcesWarehouseData).values(
                warehouse_id=data.to_warehouse_id,
                resource_amount=data.resource_amount,
                resource_id=data.resource_id,
            )
            await session.execute(query)
        # Product exists in to_warehouse_id, update amounts
        if query2_data is None:
            query2_data=0
            new_amount_from = query1_data.resource_amount - data.resource_amount
            new_amount_to = query2_data + data.resource_amount
        new_amount_from = query1_data.resource_amount - data.resource_amount
        new_amount_to = query2_data + data.resource_amount

        #update from_warehouse product_amount
        query = update(ResourcesWarehouseData).where(
            and_(ResourcesWarehouseData.warehouse_id == data.from_warehouse_id,
                 ResourcesWarehouseData.resource_id == data.resource_id)
        ).values(resource_amount=new_amount_from)
        await session.execute(query)

        query = update(ResourcesWarehouseData).where(
            and_(ResourcesWarehouseData.warehouse_id == data.to_warehouse_id,
                 ResourcesWarehouseData.resource_id == data.resource_id)
        ).values(resource_amount=new_amount_to)
        await session.execute(query)


        query3 = insert(WarehouseExchangeHistory).values(
            resource_id=data.resource_id,
            from_warehouse_id=data.from_warehouse_id,
            to_warehouse_id=data.to_warehouse_id
        )
        await session.execute(query3)
        await session.commit()

        return {"message": "Exchange successful"}
    raise HTTPException(status_code=400, detail="At least one item should be added")


@warehouse_router.post('/create-reciept')
async def create_reciept(
        data: ShiftScheme,
        session: AsyncSession = Depends(get_async_session),
):
    try:
        query = insert(Reciept).values(**data.dict()).returning(Reciept.id)
        id = await session.execute(query)
        id = id.scalar()
        await session.commit()
        return {'succes':True, 'message':f'Reciept id {id}'}
    except HTTPException as e:
        raise HTTPException(status_code=400, detail=str(e))


@warehouse_router.post('/add-reciept')
async def add_reciept(
        data: AddResieptScheme,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query = insert(RecieptForProducts).values(**data.dict())
        await session.execute(query)
        await session.commit()
        return {'status':True, "detail":"Reciept added successfully"}
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e))



@warehouse_router.get('/get-reciept', response_model=List[GetRecieptsScheme])
async def get_reciept(
        product_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    query = (select(RecieptForProducts)
             .options(selectinload(RecieptForProducts.resources))
             .where(RecieptForProducts.product_id == product_id))
    result = await session.execute(query)
    product_reciept = result.scalars()

    reciept_data=[]
    for reciept in product_reciept:
        reciept_data.append({
            'resource': reciept.resources.name,
            'resource_amount': reciept.resource_amount,
        })
    return reciept_data


@warehouse_router.post('/get-resources', response_model=List[GetRecieptsScheme])
async def get_resource(
        data: GetResourcesScheme,
        session: AsyncSession = Depends(get_async_session)
):
    product_reciept = (select(RecieptForProducts)
             .options(selectinload(RecieptForProducts.resources))
             .where(RecieptForProducts.reciept_id == data.reciept_id))
    product_reciept_data = await session.execute(product_reciept)
    reciept_data = product_reciept_data.scalars()

    check_resources = (select(ResourcesWarehouseData)
                       .options(selectinload(ResourcesWarehouseData.resource))
                       .where(ResourcesWarehouseData.warehouse_id == data.warehouse_id))

    resources_in_warehouse = await session.execute(check_resources)
    resources_in_warehouse_data = resources_in_warehouse.scalars()


    reciept_amount = []
    for reciept in reciept_data:
        new_amount = reciept.resource_amount * data.amount
        reciept_amount.append({
            'resource': reciept.resources.name,
            'resource_amount': new_amount,
            'resource_id': reciept.resource_id
        })

    for resource in resources_in_warehouse_data:
        for reciept in reciept_amount:
            new = reciept['resource_amount'] * data.amount
            new_amount = resource.resource_amount - new
            if resource.resource.name == reciept['resource'] and resource.resource_amount >= new:

                query = (
                    update(ResourcesWarehouseData)
                    .where(
                        and_(ResourcesWarehouseData.resource_id == reciept['resource_id'],
                        ResourcesWarehouseData.warehouse_id == data.warehouse_id)
                    )
                    .values(
                        resource_amount=new_amount
                    )
                )
                await session.execute(query)
                break
        else:
            # If the resource is not enough, raise an exception
            raise HTTPException(status_code=400, detail="Resource not enough")
    await session.commit()

    return reciept_amount