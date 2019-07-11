import logging
from datetime import datetime, timedelta
from typing import List

from sqdc import SqdcStore
from sqdc.dataobjects.product import Product
from sqdc.dataobjects.productevent import ProductEvent

log = logging.getLogger(__name__)

DUPLICATE_IN_STOCK_DURATION_MINUTES = 12 * 60


def find_by_id(lookup_list: List[Product], product, match_predicate=lambda x: True) -> Product:
    if product is None:
        raise AttributeError

    if isinstance(product, int) or isinstance(product, str):
        product_id = str(product)
    else:
        product_id = product.id

    return next((p for p in lookup_list if p.id == product_id and match_predicate(p)), None)


class ProductCalculator:
    store: SqdcStore

    def __init__(self, store: SqdcStore, previous_products: List[Product], updated_products: List[Product]):
        self.store = store
        self.updated_products = updated_products
        self.previous_products = previous_products

    def get_became_out_of_stock(self):
        return sorted([p for p in self.updated_products if not p.is_in_stock() and find_by_id(self.previous_products, p, lambda p: p.is_in_stock())],
                      key=lambda p: p.get_sorting_key())

    def get_became_in_stock(self):
        return sorted([p
                       for p
                       in self.updated_products
                       if p.is_in_stock()
                       and not find_by_id(self.previous_products, p, lambda x: x.is_in_stock())],
                      key=lambda p: p.get_sorting_key())

    def was_product_recently_in_stock(self, product: Product):
        last_in_stock = self.store.get_last_in_stock_product_history(product_id=product.id, event=ProductEvent.IN_STOCK)
        time_since_last_in_stock = datetime.now() - last_in_stock.timestamp if last_in_stock else datetime.min
        was_in_stock_recently = last_in_stock and time_since_last_in_stock < timedelta(minutes=DUPLICATE_IN_STOCK_DURATION_MINUTES)
        return was_in_stock_recently

    def get_new_products(self):
        return sorted([p for p in self.updated_products if p.is_in_stock() and not find_by_id(self.previous_products, p)], key=lambda p: p.get_sorting_key())
