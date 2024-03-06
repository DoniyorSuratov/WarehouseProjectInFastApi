from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from auth.utils import verify_token
from database import get_async_session
from models.models import Users, Categories, Role, Products
from .schemes import CategoryAddScheme, UserRoleScheme, ProductScheme

admin_router = APIRouter()


#Only admin can add role admins role_id should be 1
@admin_router.post('/add-role')
async def add_role(data: UserRoleScheme,
                   session: AsyncSession = Depends(get_async_session),
                   token: dict = Depends(verify_token)
                   ):
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = token.get('user_id')

    query = select(Users).where(Users.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one()
    if user.role_id == 1:
        dict_role = UserRoleScheme(**dict(data))
        dict_role_ = dict_role.dict()
        add_role = insert(Role).values(dict_role_)
        await session.execute(add_role)
        await session.commit()
    else:
        raise HTTPException(status_code=400, detail="You have not permission")
    return {'success': True, 'message': 'Role added'}


@admin_router.post('/add-category')
async def add_product(data: CategoryAddScheme,
                      token: dict = Depends(verify_token),
                      session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = select(Users).where(Users.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one()
    if user.role_id == 1:
        dict_category = CategoryAddScheme(**dict(data))
        dict_category_ = dict_category.dict()
        category = insert(Categories).values(**dict_category_)
        await session.execute(category)
        await session.commit()
    else:
        raise HTTPException(status_code=400, detail="You have not permission")
    return {"status": True, 'message': 'Category added successfully'}


@admin_router.post('/add-product')
async def add_product(
        data: ProductScheme,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    user_id = token.get('user_id')
    if token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    query = select(Users).where(Users.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one()
    if user.role_id == 1:
        dict_product = ProductScheme(**dict(data))
        dict_product_ = dict_product.dict()
        product = insert(Products).values(**dict_product_)
        await session.execute(product)
        await session.commit()
    else:
        raise HTTPException(status_code=400, detail="You have no permission")
    return {"status": True, 'message': 'Product sucessfully added'}