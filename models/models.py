from datetime import datetime
from sqlalchemy import (
    Column,
    Table,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    MetaData,
    TIMESTAMP
)
from database import Base
from sqlalchemy.orm import relationship

metadata = MetaData()

class Role(Base):
    __tablename__ = 'role'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, unique=True)

class Categories(Base):
    __tablename__ = 'categories'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class Users(Base):
    __tablename__ = "users"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=True)
    password = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey('role.id'), default=2)


class Products(Base):
    __tablename__ = "products"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)


class ShoppingCart(Base):
    __tablename__ = "shoppingcart"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    count = Column(Integer, default=1)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    order_id = Column(Integer, nullable=True)


class Order(Base):
    __tablename__ = "order"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    cart_id = Column(Integer,  nullable=True)
    total_debt = Column(Float, nullable=True)
    paid = Column(Float, default=0)
    hash = Column(String, nullable=False)


class WarehouseCategory(Base):
    __tablename__ = 'warehouse_category'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)


class Warehouse(Base):
    __tablename__ = 'warehouse'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column('name', String)
    category_id = Column(Integer, ForeignKey('warehouse_category.id'))
    latitude = Column('latitude', Float)
    longitude = Column('longitude', Float)


class WarehouseData(Base):
    __tablename__ = 'warehouse_data'
    metadata = metadata
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column('warehouse_id', Integer, ForeignKey('warehouse.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float, nullable=False)
    amount = Column(Integer)


class ProductHistory(Base):
    __tablename__ = 'product_history'
    metadata = metadata
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    product_id = Column('product_id', Integer, ForeignKey('products.id'))
    warehouse1_id = Column('warehouse1_id', Integer, ForeignKey('warehouse.id'))
    warehouse2_id = Column('warehouse2_id', Integer, ForeignKey('warehouse.id'))
    last_update = Column('last_update', TIMESTAMP, default=datetime.utcnow())