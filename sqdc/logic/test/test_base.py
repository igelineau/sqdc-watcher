from unittest import TestCase

from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_variant import ProductVariant


class TestBase(TestCase):
    product_counter: int
    variant_counter: int

    def setUp(self):
        self.product_counter = 0
        self.variant_counter = 0

    def create_products(self, number: int):
        products = []
        for i in range(number):
            products.append(self.create_product())
        return products

    def create_product(self, in_stock=True, **kwargs) -> Product:
        product = Product(id=self.product_counter, in_stock=in_stock, **kwargs)
        product.variants.append(self.create_variant(product.id))

        self.product_counter += 1
        print('created product: ', product.as_dict())
        return product

    def create_variant(self, product_id, in_stock=True) -> ProductVariant:
        variant = ProductVariant(id=self.variant_counter, product_id=product_id, in_stock=in_stock)
        self.variant_counter += 1
        return variant
