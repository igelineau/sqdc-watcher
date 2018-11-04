from tabulate import tabulate


class SqdcFormatter:

    @staticmethod
    def format_product(product):
        in_stock_str = 'In stock' if product['in_stock'] else 'Out of stock'
        variants_in_stock = [v for v in product['variants'] if v['in_stock']]
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent']['Value'])) + ' g' for v in variants_in_stock])
        return '[{}] - {} ({}), quantities available: {}'.format(in_stock_str, product['title'], product['brand'],
                                                                 variants_descriptions)

    @staticmethod
    def format_variants_available(product):
        variants_in_stock = [v for v in product['variants'] if v['in_stock']]
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent']['Value'])) + ' g' for v in variants_in_stock])
        return variants_descriptions

    @staticmethod
    def format_brand_and_supplier(product):
        variant_with_specifications = [v for v in product['variants'] if 'specifications' in v][0]
        brand = product['brand']
        producer_name = variant_with_specifications['specifications']['ProducerName']['Value']
        display_string = brand
        if producer_name != brand:
            display_string += ' (' + producer_name + ')'

        return display_string

    @staticmethod
    def build_products_table(products):
        headers = [
            'Name',
            'In Stock',
            'Brand',
            'Formats available',
            'URL'
        ]
        tabulated_data = [
            [p['title'],
             p['in_stock'],
             SqdcFormatter.format_brand_and_supplier(p),
             SqdcFormatter.format_variants_available(p),
             p['url']] for p in products]
        return tabulate(tabulated_data, headers=headers)
