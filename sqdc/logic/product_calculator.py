from typing import List

from sqdc.dataobjects.product import Product


class ProductCalculator:
    def __init__(self, previous_products: List[Product], updated_products: List[Product]):
        """
        :type updated_products: object - Must contain only in-stock products (the code relies on this to work)
        """
        self.updated_products = updated_products
        self.previous_products = previous_products

    def get_became_out_of_stock(self):
        return [p for p in self.previous_products if p.is_in_stock() and not ProductCalculator.find_by_id(self.updated_products, p)]

    def get_became_in_stock(self):
        return [p for p in self.updated_products if p.is_in_stock() and not ProductCalculator.find_by_id(self.previous_products, p, lambda x: x.is_in_stock())]

    def get_new_products(self):
        return [p for p in self.updated_products if p.is_in_stock() and not ProductCalculator.find_by_id(self.previous_products, p)]

    @staticmethod
    def find_by_id(lookup_list: List[Product], product: Product,  match_predicate=lambda x: True):
        return len([p for p in lookup_list if p.id == product.id and match_predicate(p)]) > 0
