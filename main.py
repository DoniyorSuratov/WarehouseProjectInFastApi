from fastapi import FastAPI

from admin.admin import admin_router
from auth.accounts import register_router
from shop.shop import shop_router
from warehouse.warehouse import warehouse_router

app = FastAPI()


app.include_router(register_router, prefix='/auth')
app.include_router(shop_router, prefix='/shop')
app.include_router(admin_router, prefix='/admin')
app.include_router(warehouse_router, prefix='/warehouse')