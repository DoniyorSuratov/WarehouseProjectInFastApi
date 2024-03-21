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
    TIMESTAMP,
    Text, UniqueConstraint
)
from database import Base
from sqlalchemy.orm import relationship

metadata = MetaData()

class Role(Base):
    __tablename__ = 'role'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, unique=True)

    users = relationship('Users', back_populates='role')

class Categories(Base):
    __tablename__ = 'categories'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    product = relationship("Products", back_populates="category")
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
    machine_id = Column(Integer, ForeignKey('machine.id'), nullable=True)
    shift_id = Column(Integer, ForeignKey('shift.id'))


    machine = relationship('Machine', back_populates='users')
    shift = relationship("Shift", back_populates='users')
    role = relationship("Role", back_populates='users')
    shopping_cart = relationship('ShoppingCart', back_populates='user')
    order = relationship('Order', back_populates='user')

class Products(Base):
    __tablename__ = "products"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)

    shopping_cart = relationship('ShoppingCart',back_populates='product')
    category = relationship("Categories", back_populates="product")
    warehouse_exchange = relationship("WarehouseData", back_populates='product')
    warehouse_exchange_data = relationship('WarehouseExchangeHistory', back_populates='product')
    reciept_for_products = relationship('RecieptForProducts', back_populates='product')

class ShoppingCart(Base):
    __tablename__ = "shoppingcart"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    count = Column(Integer, default=1)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    order_id = Column(Integer, ForeignKey("order.id"),nullable=True)

    product = relationship("Products", back_populates="shopping_cart")
    order = relationship('Order', back_populates='cart')
    user = relationship('Users', back_populates='shopping_cart')
    warehouse = relationship('Warehouse', back_populates='shopping_cart')


class Order(Base):
    __tablename__ = "order"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_debt = Column(Float, nullable=True)
    paid = Column(Float, default=0)
    hash = Column(String, nullable=False)

    user = relationship('Users', back_populates='order')
    cart = relationship('ShoppingCart', back_populates='order')
    


class WarehouseCategory(Base):
    __tablename__ = 'warehouse_category'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    warehouse = relationship('Warehouse', back_populates="category")


class WarehouseData(Base):
    __tablename__ = 'warehouse_data'
    metadata = metadata
    id = Column( Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    price = Column(Float, nullable=False)
    amount = Column(Integer)

    warehouse = relationship('Warehouse', back_populates='warehouse_data')
    product = relationship('Products', back_populates='warehouse_exchange')


class Warehouse(Base):
    __tablename__ = 'warehouse'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column('name', String)
    category_id = Column(Integer, ForeignKey('warehouse_category.id'))
    latitude = Column('latitude', Float)
    longitude = Column('longitude', Float)

    category = relationship('WarehouseCategory', back_populates='warehouse')
    shopping_cart = relationship('ShoppingCart', back_populates='warehouse')
    warehouse_data = relationship('WarehouseData', back_populates='warehouse')
    warehouse_data_resources = relationship('ResourcesWarehouseData', back_populates='warehouse')

class WarehouseExchangeHistory(Base):
    __tablename__ = 'warehouse_exchange_history'
    metadata = metadata
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    product_id = Column('product_id', Integer, ForeignKey('products.id'), nullable=True)
    resource_id = Column( Integer, ForeignKey('resources.id'), nullable=True)
    from_warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    to_warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    last_update = Column('last_update', TIMESTAMP, default=datetime.utcnow())


    product = relationship('Products', back_populates='warehouse_exchange_data')
    resource = relationship('Resources', back_populates='warehouse_exchange_data')

class DeletedProductsWarehouse(Base):
    __tablename__ = 'deleted_products_warehouse'
    metadata = metadata
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    product_id = Column('product_id', Integer, ForeignKey('products.id'))
    warehouse_id = Column('warehouse_id', Integer, ForeignKey('warehouse.id'))
    reason = Column('reason', Text, nullable=False)
    user_id = Column('user_id', Integer, ForeignKey('users.id'))
    last_update = Column('last_update', TIMESTAMP, default=datetime.utcnow())


class Machine(Base):
    __tablename__ = 'machine'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    users = relationship("Users", back_populates="machine")


class Shift(Base):
    __tablename__ = 'shift'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    users = relationship("Users", back_populates='shift')


class Resources(Base):
    __tablename__ = 'resources'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    resource_warehouse_data =relationship("ResourcesWarehouseData", back_populates='resource')
    warehouse_exchange_data = relationship("WarehouseExchangeHistory", back_populates='resource')
    reciept_for_products = relationship('RecieptForProducts', back_populates='resources')

class ResourcesWarehouseData(Base):
    __tablename__ = 'resources_warehouse_data'
    metadata = metadata
    id = Column( Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer,ForeignKey('resources.id'), nullable=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    resource_amount = Column(Float, nullable=True)

    warehouse = relationship('Warehouse', back_populates='warehouse_data_resources')
    resource = relationship('Resources', back_populates='resource_warehouse_data')


class Reciept(Base):
    __tablename__ = 'reciept'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    reciept_for_products = relationship('RecieptForProducts', back_populates='reciept')


class RecieptForProducts(Base):
    __tablename__ = 'reciept_for_products'
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    reciept_id = Column(Integer, ForeignKey('reciept.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    resource_id = Column(Integer, ForeignKey('resources.id'))
    resource_amount = Column(Float, nullable=True)

    UniqueConstraint('reciept_id', 'resource_id', 'product_id', name='unique_constraint_reciept')

    reciept = relationship('Reciept', back_populates='reciept_for_products')
    product = relationship('Products', back_populates='reciept_for_products')
    resources = relationship('Resources', back_populates='reciept_for_products')