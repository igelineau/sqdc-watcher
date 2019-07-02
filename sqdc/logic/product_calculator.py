from typing import List

from sqdc.dataobjects.product import Product
from sqdc.dto.product_stock_differences import ProductStockDifferences


class ProductCalculator:
    def __init__(self, previous_products: List[Product], current_products: List[Product]):
        self.current_products = current_products
        self.previous_products = previous_products

    def calculate_stock_differences(self):
        became_in_stock = self.product_difference(self.previous_products, self.current_products)
        became_out_of_stock = self.product_difference(self.current_products, self.previous_products)
        return ProductStockDifferences(became_in_stock, became_out_of_stock)

    def product_difference(self, left_operand: List[Product], right_operand: List[Product]):
        prev_ids = set([p.id for p in left_operand if p.is_in_stock()])
        cur_ids = set([p.id for p in right_operand if p.is_in_stock()])
        new_products = [pid
                        for pid in cur_ids
                        if pid not in prev_ids]
        return [p for p in right_operand if p.id in new_products]