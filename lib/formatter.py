import re
from typing import List

from tabulate import tabulate
from .product import Product


class SqdcFormatter:

    @staticmethod
    def format_products(products: List[Product], display_format='table'):
        if display_format == 'table':
            return SqdcFormatter.build_products_table(products)
        elif display_format == 'list':
            return '\n'.join([SqdcFormatter.format_product(p) for p in products])

    @staticmethod
    def format_product(product: Product):
        return '*{}* / {} - ({} {}) {}'.format(
            SqdcFormatter.format_name_with_type(product),
            product.get_property('brand'),
            SqdcFormatter.format_category(product),
            SqdcFormatter.format_variants_available(product),
            SqdcFormatter.format_url(product))

    @staticmethod
    def format_variants_available(product: Product):
        variants_in_stock = product.get_variants_in_stock()
        quantities = sorted([float(v['specifications']['GramEquivalent']) for v in variants_in_stock])
        variants_descriptions = ', '.join([SqdcFormatter.trim_zeros(quantity) + 'g' for quantity in quantities])
        return variants_descriptions

    @staticmethod
    def format_brand_and_supplier(product: Product):
        producer_name = product.get_specification('ProducerName')
        brand = product.get_property('brand')
        components = []
        if SqdcFormatter.should_display_brand(brand):
            components.append(brand)
        if SqdcFormatter.should_display_supplier(producer_name) and producer_name != brand:
            components.append(producer_name)
        if len(components) == 0:
            components.append(brand)

        display_string = components[0]
        if len(components) > 1:
            display_string += ' (' + components[1] + ')'

        return display_string

    @staticmethod
    def should_display_brand(brand):
        return brand not in ['Plain Packaging']

    @staticmethod
    def should_display_supplier(supplier):
        return supplier not in ['Aurora Cannabis']

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
            raw_cbd_min = product.get_specification('CBDContentMin')
            raw_cbd_max = product.get_specification('CBDContentMax')
            return SqdcFormatter.format_cannabinoid_concentration(product, raw_cbd_min, raw_cbd_max)

    @staticmethod
    def format_thc(product: Product):
        if product.has_specifications():
            raw_thc_min = product.get_specification('THCContentMin')
            raw_thc_max = product.get_specification('THCContentMax')
            return SqdcFormatter.format_cannabinoid_concentration(product, raw_thc_min, raw_thc_max)

    @staticmethod
    def format_cannabinoid_concentration(product, min_value, max_value):
        unit_of_measure = product.get_specification('UnitOfMeasureThcCbd')
        min_int = int(float(min_value))
        max_int = int(float(max_value))
        formatted_value_or_range = '{}'.format(min_int) if min_int == max_int else '{min} - {max}'.format(min=min_int,
                                                                                                          max=max_int)
        if formatted_value_or_range != '0':
            formatted_value_or_range += unit_of_measure
        return formatted_value_or_range

    @staticmethod
    def format_type(product: Product):
        return product.get_specification('CannabisType')

    @staticmethod
    def format_url(product):
        url = product.get_property('url').replace('www.', '')
        # remove the variant path component
        url = re.sub(r'(.+/\d+-P)(/\d+)', r'\1', url)
        return url

    @staticmethod
    def build_products_table(products: List[Product], prepend_with_newline=True):
        headers = [
            'Name',
            'Brand',
            'Category',
            'Type',
            'THC',
            'CBD',
            'avail. formats',
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
             SqdcFormatter.format_url(p)] for p in products]
        prefix = '\n' if prepend_with_newline else ''
        return prefix + tabulate(tabulated_data, headers=headers) + '\n'

    @staticmethod
    def format_category(product: Product):
        return product.get_specification('LevelTwoCategory')

    @staticmethod
    def trim_zeros(text):
        return '' if text is None else str.format('{}', text).rstrip('0').rstrip('.').rjust(2)
