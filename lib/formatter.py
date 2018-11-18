from typing import List

from tabulate import tabulate
from .product import Product


class SqdcFormatter:

    @staticmethod
    def format_product(product: Product):
        variants_in_stock = product.get_variants_in_stock()
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent'])) + ' g' for v in variants_in_stock])
        url = product.get_property('url').replace('www.', '')

        return '*{}* / {} - ({}) {}'.format(
            SqdcFormatter.format_name_with_type(product),
            product.get_property('brand'),
            variants_descriptions,
            url)

    @staticmethod
    def format_variants_available(product: Product):
        variants_in_stock = product.get_variants_in_stock()
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent'])) + ' g' for v in variants_in_stock])
        return variants_descriptions

    @staticmethod
    def format_brand_and_supplier(product: Product):
        producer_name = product.get_specification('ProducerName')
        brand = product.get_property('brand')
        display_string = brand
        if producer_name != brand:
            display_string += ' (' + producer_name + ')'

        return display_string

    @staticmethod
    def format_name(product):
        name = product.get_property('title')
        strain = product.get_specification('Strain')
        if strain and strain.lower() != name.lower():
            name = '{} ({})'.format(strain, name)
        return name

    @staticmethod
    def format_name_with_type(product):
        name = SqdcFormatter.format_name(product)
        cannabis_type = product.get_specification('CannabisType')
        if cannabis_type:
            name = name + ', ' + cannabis_type
        return name

    @staticmethod
    def format_cbd(product):
        if product.has_specifications():
            cbd_min = float(product.get_specification('CBDContentMin'))
            cbd_max = float(product.get_specification('CBDContentMax'))
            cbd = '0' if cbd_min == 0 else '{:>4.1f}-{:>4.1f}'.format(cbd_min, cbd_max)
            return cbd

    @staticmethod
    def format_thc(product: Product):
        if product.has_specifications():
            thc_min = float(product.get_specification('THCContentMin'))
            thc_max = float(product.get_specification('THCContentMax'))
            thc = '0' if thc_min == 0 else '{:>4.1f}-{:>4.1f}'.format(thc_min, thc_max)
            return thc

    @staticmethod
    def format_type(product: Product):
        return product.get_specification('CannabisType')

    @staticmethod
    def build_products_table(products: List[Product], prepend_with_newline=True):
        headers = [
            'Name',
            'Brand',
            'Category',
            'Type',
            'THC',
            'CBD',
            'Formats available',
            'URL'
        ]
        tabulated_data = [
            [SqdcFormatter.format_name(p),
             SqdcFormatter.format_brand_and_supplier(p),
             SqdcFormatter.format_category(p),
             SqdcFormatter.format_type(p),
             SqdcFormatter.format_thc(p),
             SqdcFormatter.format_cbd(p),
             SqdcFormatter.format_variants_available(p),
             p.get_property('url')] for p in products]
        prefix = '\n' if prepend_with_newline else ''
        return prefix + tabulate(tabulated_data, headers=headers) + '\n'

    @staticmethod
    def format_category(product: Product):
        return product.get_specification('LevelTwoCategory')
