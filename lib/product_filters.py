from typing import List

from lib.stores.product import Product


class ProductFilters:
    @staticmethod
    def in_stock(products_list: List[Product]):
        return [p for p in products_list if p.is_in_stock()]
