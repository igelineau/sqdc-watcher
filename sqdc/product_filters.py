from typing import List

from sqdc.dataobjects.product import Product


class ProductFilters:
    @staticmethod
    def in_stock(products_list: List[Product]):
        return sorted([p for p in products_list if p.is_in_stock()], key=lambda p: p.get_sorting_key())
