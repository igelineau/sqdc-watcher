from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from sqdc.dataobjects.base import Base
from sqdc.dataobjects.product_variant import ProductVariant


class Product(Base):
    __tablename__ = 'products'

    id = Column(String(50), primary_key=True)
    created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    title = Column(String)
    url = Column(String, nullable=False)
    in_stock = Column(Boolean)
    brand = Column(String)

    variants = relationship('ProductVariant', lazy='joined')

    def has_specifications(self):
        return self.find_variant_with_specs() is not None

    def get_specification(self, key):
        variant_with_spec = self.find_variant_with_specs()
        return '' if variant_with_spec is None else variant_with_spec.specifications.get(key)

    def find_variant_with_specs(self):
        return next((v for v in self.variants if v.specifications is not None), None)

    def is_in_stock(self):
        return self.in_stock and len(self.get_variants_in_stock()) > 0

    def get_variants_in_stock(self):
        return [v for v in self.variants if v.in_stock]

    def get_property(self, name) -> str:
        return self.data[name]

    def __repr__(self):
        return f'Product(id={self.id}, title={self.title}, in_stock={self.in_stock}, {self.variants} variants)'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
