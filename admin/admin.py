from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.utils import verify_token
from database import get_async_session
from models.models import Users, Categories, Role, Products
from warehouse.utils import is_admin
from .schemes import CategoryAddScheme, UserRoleScheme, ProductScheme, UserMachineScheme, AddShiftScheme

admin_router = APIRouter()


@admin_router.post('/add-role')
async def add_role(data: UserRoleScheme,
                   session: AsyncSession = Depends(get_async_session),
                   token: dict = Depends(is_admin)
):
    dict_role = UserRoleScheme(**dict(data))
    dict_role_ = dict_role.dict()
    add_role = insert(Role).values(dict_role_)
    await session.execute(add_role)
    await session.commit()
    return {'success': True, 'message': 'Role added'}


@admin_router.post('/add-category')
async def add_product(data: CategoryAddScheme,
                      token: dict = Depends(is_admin),
                      session: AsyncSession = Depends(get_async_session)):

    dict_category = CategoryAddScheme(**dict(data))
    dict_category_ = dict_category.dict()
    category = insert(Categories).values(**dict_category_)
    await session.execute(category)
    await session.commit()
    return {"status": True, 'message': 'Category added successfully'}


@admin_router.post('/add-product')
async def add_product(
        data: ProductScheme,
        token: dict = Depends(is_admin),
        session: AsyncSession = Depends(get_async_session)
):
    dict_product = ProductScheme(**dict(data))
    dict_product_ = dict_product.dict()
    product = insert(Products).values(**dict_product_)
    await session.execute(product)
    await session.commit()
    return {"status": True, 'message': 'Product sucessfully added'}


@admin_router.post('/add-machinery')
async def add_product(
        data: UserMachineScheme,
        token: dict = Depends(is_admin),
        session: AsyncSession = Depends(get_async_session)
):
    query = select(Users).options(selectinload(Users.role)).where(Users.username==data.username)
    result = await session.execute(query)
    user = result.scalar()
    if user.role.role != 'worker':
        return {"status":400, "message": "You can not add machine to this user"}
    query2 = update(Users).where(Users.username == data.username).values(machine_id=data.machine_id)
    await session.execute(query2)
    await session.commit()
    return {"status": 200, "message": "Machine added successfully"}


@admin_router.post('/add-shift')
async def add_product(
        data: AddShiftScheme,
        token: dict = Depends(is_admin),
        session: AsyncSession = Depends(get_async_session)
):
    try:
        query2 = update(Users).where(Users.username == data.username).values(shift_id=data.shift_id)
        await session.execute(query2)
        await session.commit()
        return {"status": 200, "message": "Machine added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))