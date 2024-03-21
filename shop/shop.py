import secrets
from typing import List
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.operators import and_

from admin.schemes import UserRoleScheme
from auth.accounts import user_info
from auth.schemes import UserOutDB, UserOutDBScheme
from auth.utils import verify_token, get_user_info_by_id, get_shopping_cart_by_order
from database import get_async_session
from models.models import Users, Categories, Products, ShoppingCart, Order, WarehouseData
from warehouse.schemes import ShiftScheme, MachineScheme
from .schemes import AllProductsScheme, ProductsScheme, PaymentScheme, ConfirmScheme, OrderScheme

shop_router = APIRouter()


@shop_router.get("/get-products", response_model=List[AllProductsScheme])
async def get_products(session: AsyncSession = Depends(get_async_session)):
    try:
        data = select(Products).options(selectinload(Products.category))
        products = await session.execute(data)
        products_data = products.scalars()

        result = []
        for product in products_data:
            result.append(
                AllProductsScheme(
                    name=product.name,
                    category=product.category.name
                )
            )
        return result
    except NoResultFound:
        raise HTTPException(status_code=400, detail="Product not found")



@shop_router.post("/create-order")
async def create_order(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    user_id = token.get('user_id')
    hashed = secrets.token_hex(10)
    query = insert(Order).values(hash=hashed, user_id=user_id).returning(Order.id)
    result = await session.execute(query)
    order_id = result.scalar_one()
    await session.commit()
    return {"success": True, "hash": hashed, "order_id": order_id}


@shop_router.post("/add-to-cart")
async def add_product(
        data: ProductsScheme,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    query = select(Order.id).where(Order.hash == data.hash)
    order_id = await session.execute(query)
    order_id = order_id.scalar_one()

    pro_query = select(WarehouseData.amount).where(and_(WarehouseData.product_id == data.product_id,
                                                        WarehouseData.warehouse_id == data.warehouse_id))
    product_amount = await session.execute(pro_query)
    product_amount = product_amount.scalar_one()

    try:
        if order_id and product_amount:
            if product_amount > data.count:
                cart_query = insert(ShoppingCart).values(user_id=user_id, product_id=data.product_id, count=data.count, order_id=order_id, warehouse_id=data.warehouse_id)
                await session.execute(cart_query)
                await session.commit()
                return {"success": True, "message": "Product added to cart"}

    except NoResultFound:
        raise HTTPException(status_code=404, detail="Product or Order does not exist in this warehouse")



@shop_router.post("/confirm-order")
async def confirm_order(
        data: ConfirmScheme,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):

    query = select(Products).join(ShoppingCart, Products.id == ShoppingCart.product_id).where(
        ShoppingCart.order_id == data.order_id)
    product_data = await session.execute(query)
    product_data = product_data.scalars().all()

    query = select(WarehouseData).join(ShoppingCart, WarehouseData.product_id == ShoppingCart.product_id).where(
        ShoppingCart.order_id == data.order_id)
    warehouse_data = await session.execute(query)
    warehouse_sum = warehouse_data.scalars().all()

    query2 = select(ShoppingCart).join(Products, ShoppingCart.product_id == Products.id).where(
        ShoppingCart.order_id == data.order_id)
    cart_data = await session.execute(query2)
    cart_data = cart_data.scalars().all()

    # Calculate total price
    total_price = sum(product.price * cart.count for product, cart in zip(warehouse_sum, cart_data))

    query3 = update(Order).where(Order.hash == data.hash).values(total_debt=total_price)
    await session.execute(query3)

    for product, cart in zip(warehouse_sum, cart_data):
        new_amount = product.amount - cart.count

        if new_amount < 0:
            raise HTTPException(status_code=400, detail=f"Not enough products in stock. Available: {product.amount}")

        query4 = update(WarehouseData).where(
            (WarehouseData.product_id == cart.product_id) &
            (WarehouseData.warehouse_id == cart.warehouse_id)
        ).values(amount=new_amount)

        await session.execute(query4)

    await session.commit()

    return {"message": "Order confirmed successfully"}


@shop_router.get("/all-my-orders", response_model=List[OrderScheme])
async def my_orders(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    try:
        user_id = token.get("user_id")

        # Join Order and ShoppingCart tables to filter based on user_id
        query = select(Order).join(ShoppingCart).options(
            selectinload(Order.user),
            selectinload(Order.cart)
        ).filter(
            Order.user_id == user_id,
            ShoppingCart.user_id == user_id,
            ShoppingCart.order_id == Order.id
        )

        data = await session.execute(query)
        orders = data.scalars().all()

        my_orders_list = []
        seen_order_ids = set()
        for order in orders:
            if order.id not in seen_order_ids:
                shopping_cart_items = await get_shopping_cart_by_order(order.user_id, order.id, session)
                my_orders_list.append(OrderScheme(
                    user=await get_user_info_by_id(order.user_id, session),
                    cart=shopping_cart_items,
                    total_debt=order.total_debt,
                    paid=order.paid,
                    hash=order.hash
                ))
                seen_order_ids.add(order.id)

        return my_orders_list
    except Exception as e:
        raise HTTPException(status_code=400, detail="Orders not found")


@shop_router.post("/payment")
async def create_payment(
        data: PaymentScheme,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
        ):
    query = select(Order.total_debt).where(Order.id == data.order_id)
    my_order = await session.execute(query)
    total_debt = my_order.scalar_one()
    if total_debt < data.payment:
        summ = data.debt - total_debt
        return {"You paid more then expected": summ}
    else:
        summ = total_debt - data.payment
    query = update(Order).where(Order.id == data.order_id).values(total_debt=summ, paid=data.payment)
    await session.execute(query)
    await session.commit()

    return {"status": True,"message": "Payment successful"}



