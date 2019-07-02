import unittest

from sqdc.logic.product_calculator import ProductCalculator
from sqdc.logic.test.test_base import TestBase


class ProductCalculatorTests(TestBase):

    def test_product_became_in_stock(self):
        prev_producs = self.create_products(5)
        current_products = prev_producs.copy()
        print(prev_producs)

        new_product = self.create_product()
        current_products.append(new_product)
        calculator = ProductCalculator(prev_producs, current_products)
        differences = calculator.calculate_stock_differences()

        self.assertIs(len(differences.became_in_stock), 1)
        self.assertIs(len(differences.became_out_of_stock), 0)

    def test_product_became_out_of_stock(self):
        prev_producs = self.create_products(5)
        current_products = prev_producs.copy()

        current_products.remove(current_products[0])
        calculator = ProductCalculator(prev_producs, current_products)
        differences = calculator.calculate_stock_differences()

        self.assertIs(len(differences.became_out_of_stock), 1)

        self.assertIs(len(differences.became_in_stock), 0)