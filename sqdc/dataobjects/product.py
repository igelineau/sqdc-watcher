from datetime import datetime
from typing import List

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
    last_in_stock_notification = Column(DateTime)
    category = Column(String)
    cannabis_type = Column(String)
    producer_name = Column(String)

    is_new = Column(Boolean, default=True)
    availability_stats = Column(String)

    variants = relationship('ProductVariant', lazy='subquery', back_populates='product')

    def has_specifications(self) -> bool:
        return self.find_variant_with_specs() is not None

    def get_specification(self, key) -> str:
        variant_with_spec = self.find_variant_with_specs()
        return '' if variant_with_spec is None else variant_with_spec.specifications.get(key)

    def find_variant_with_specs(self) -> ProductVariant:
        return next((v for v in self.variants if v.specifications), None)

    def is_in_stock(self) -> bool:
        return len(self.get_variants_in_stock()) > 0

    def get_variants_in_stock(self) -> List[ProductVariant]:
        return [v for v in self.variants if v.in_stock]

    def get_variant(self, variant_id) -> ProductVariant:
        return next((v for v in self.variants if v.id == variant_id), None)

    def get_property(self, name) -> str:
        return self.data[name]

    def __repr__(self):
        return f'id={self.id}, title={self.title}, {self.category}, in_stock={self.in_stock}, brand={self.brand}, {len(self.variants)} : {len(self.get_variants_in_stock())} variants)'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_sorting_key(self):
        return ('1' if self.is_new else '0') + (self.category or '') + (self.producer_name or '') + (self.brand or '')
