from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth.utils import verify_token
from database import get_async_session
from models.models import Users, Categories, Role, Products
from warehouse.utils import is_admin
from .schemes import CategoryAddScheme, UserRoleScheme, ProductScheme

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