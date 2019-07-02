from datetime import datetime
from sqlalchemy import Integer, Column, ForeignKey, String, DateTime

from lib.stores.base import Base


class ProductHistory(Base):
    __tablename__ = 'product_history'

    id = Column('id', Integer, primary_key=True, autoincrement=True)
    product_id = Column('product_id', None, ForeignKey('products.id'), nullable=False)
    variant_id = Column('variant_id', Integer, nullable=False)
    event = Column('event', String, nullable=False)
    timestamp = Column('timestamp', DateTime, default=datetime.now)
