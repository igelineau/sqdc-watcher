from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from sqdc.dataobjects.base import Base


class ProductVariant(Base):
    __tablename__ = 'product_variants'

    id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey('products.id'), primary_key=True)
    created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    in_stock = Column(Boolean)
    specifications = Column(JSON)
    list_price = Column(Float)
    price = Column(Float)
    price_per_gram = Column(Float)
    quantity_description = Column(String)
    out_of_stock_since = Column(DateTime)

    product = relationship('Product', lazy='subquery', back_populates='variants')

    def __repr__(self):
        return f'ProductVariant(id={self.id}, product={self.product.title}, in_stock={self.in_stock})'

    def detailed_description(self):
        return f'ProductVariant(id={self.id}, product={self.product.title}, in_stock={self.in_stock})\n{self.specifications}'
