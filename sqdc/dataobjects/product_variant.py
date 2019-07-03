from datetime import datetime

from sqlalchemy import Column, String, DateTime, Numeric, Boolean, ForeignKey, JSON

from sqdc.dataobjects.base import Base


class ProductVariant(Base):
    __tablename__ = 'product_variants'

    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.id'), primary_key=True)
    created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    in_stock = Column(Boolean)
    specifications = Column(JSON)
    list_price = Column(Numeric)
    price = Column(Numeric)
    price_per_gram = Column(Numeric)
    quantity_description = Column(String)

    def __repr__(self):
        return f'ProductVariant(id={self.id}, product_id={self.product_id}, in_stock={self.in_stock}, specifications={self.specifications})'
