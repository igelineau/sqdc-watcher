import re
from typing import List

from babel.dates import format_timedelta
from datetime import datetime
from tabulate import tabulate

from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_variant import ProductVariant

tabulate.PRESERVE_WHITESPACE = True

TITLE_MAX_WIDTH = 20
STRAIN_MAX_WIDTH = 25
SINGLE_BRANDING_MAX_WIDTH = 25
DUAL_BRANDING_MAX_COMP_WIDTH = 12


class SqdcFormatter:

    @staticmethod
    def format_products(products: List[Product], display_format='table'):
        if display_format == 'table':
            return SqdcFormatter.build_products_table(products)
        elif display_format == 'list':
            return '\n'.join([SqdcFormatter.format_product(p) for p in products])

    @staticmethod
    def format_product(product: Product):
        return '{}*{}* / {} - ({} {}) {}'.format(
            SqdcFormatter.format_new_product_prefix(product),
            SqdcFormatter.format_name_with_type(product),
            product.brand,
            SqdcFormatter.format_category(product),
            SqdcFormatter.format_variants_available(product),
            SqdcFormatter.format_url(product))

    @staticmethod
    def format_variants_available(product: Product):
        variants_in_stock: List[ProductVariant] = sorted(product.get_variants_in_stock(),
                                                         key=lambda v: float(v.specifications['GramEquivalent']))
        variants_descriptions = ', '.join(
            [SqdcFormatter.format_variant_quantity(variant.specifications['GramEquivalent']) for variant in
             variants_in_stock])
        return variants_descriptions

    @staticmethod
    def format_variant_quantity(raw_quantity: str):
        grams_float = SqdcFormatter.trim_zeros(float(raw_quantity))
        return f'{grams_float}g'

    @staticmethod
    def format_brand_and_supplier(product: Product):
        producer_name = product.get_specification('ProducerName')
        brand = product.brand
        components = []
        if SqdcFormatter.should_display_brand(brand):
            components.append(brand)
        if SqdcFormatter.should_display_supplier(producer_name) and producer_name != brand:
            components.append(producer_name)
        if len(components) == 0:
            components.append(brand)

        display_string = components[0]
        if len(components) > 1:
            display_string += ' (' + SqdcFormatter.apply_max_length(components[1], 12) + ')'
        else:
            display_string = SqdcFormatter.apply_max_length(display_string, 25)

        return display_string

    @staticmethod
    def apply_max_length(text: str, max_length: int):
        return text[:max_length] + ('...' if len(text) > max_length else '')

    @staticmethod
    def should_display_brand(brand):
        return brand not in ['Plain Packaging']

    @staticmethod
    def should_display_supplier(supplier):
        return supplier not in ['Aurora Cannabis']

    @staticmethod
    def format_name(product):
        name = product.title
        strain = SqdcFormatter.apply_max_length(product.get_specification('Strain'), STRAIN_MAX_WIDTH)
        if strain and strain.lower() != name.lower():
            if ',' in strain:
                # it's a blend, so expect a strains list. less important.
                name = '{} ({})'.format(name, strain)
            else:
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
        url = product.url.replace('www.', '')
        # remove the variant path component
        url = re.sub(r'(.+/\d+-P)(/\d+)', r'\1', url)
        return url

    @staticmethod
    def build_products_table(products: List[Product], prepend_with_newline=True):
        grid_fmt = 'fancy_grid'
        headers = [
            '% avail.',
            'Name',
            'Strain',
            'Brand',
            'Category',
            'Type',
            'formats',
            'URL'
        ]
        tabulated_data = [
            [SqdcFormatter.format_availability(p),
             SqdcFormatter.apply_max_length(p.title, TITLE_MAX_WIDTH),
             SqdcFormatter.apply_max_length(p.get_specification('Strain'), STRAIN_MAX_WIDTH),
             SqdcFormatter.format_brand_and_supplier(p),
             SqdcFormatter.apply_max_length(SqdcFormatter.format_category(p), 50),
             SqdcFormatter.format_type(p),
             SqdcFormatter.format_variants_available(p),
             SqdcFormatter.format_url(p)] for p in products]
        prefix = '\n' if prepend_with_newline else ''
        return prefix + tabulate(tabulated_data, headers=headers, tablefmt=grid_fmt) + '\n'

    @staticmethod
    def format_category(product: Product):
        return product.get_specification('LevelTwoCategory')

    @staticmethod
    def trim_zeros(text):
        return '' if text is None else str.format('{}', text).rstrip('0').rstrip('.').rjust(2)

    @staticmethod
    def format_new_product_prefix(product):
        return ':weed: *New* :weed: ' if product.is_new else ''

    @staticmethod
    def format_availability(product):
        if product.availability_stats:
            delta = format_timedelta(datetime.now() - product.created, granularity='hour')
            availability_percent = str(round(product.availability_stats)).rjust(3, ' ')
            availability = f'|{availability_percent}%'
            return f'{availability} ({delta})'
