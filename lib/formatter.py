from tabulate import tabulate


class SqdcFormatter:

    @staticmethod
    def format_product(product):
        in_stock_str = 'In stock' if product['in_stock'] else 'Out of stock'
        variants_in_stock = [v for v in product['variants'] if v['in_stock']]
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent'])) + ' g' for v in variants_in_stock])
        return '[{}] - {} ({}), quantities available: {}'.format(
            in_stock_str,
            SqdcFormatter.format_name_with_type(product),
            SqdcFormatter.format_brand_and_supplier(product),
            variants_descriptions)

    @staticmethod
    def format_variants_available(product):
        variants_in_stock = [v for v in product['variants'] if v['in_stock']]
        variants_descriptions = ', '.join(
            [str(float(v['specifications']['GramEquivalent'])) + ' g' for v in variants_in_stock])
        return variants_descriptions

    @staticmethod
    def format_brand_and_supplier(product):
        specifications = SqdcFormatter.get_product_specs(product)
        producer_name = '' if specifications is None else specifications['ProducerName']
        brand = product['brand']
        display_string = brand
        if producer_name != brand:
            display_string += ' (' + producer_name + ')'

        return display_string

    @staticmethod
    def find_variant_with_specs(product):
        return next((v for v in product['variants'] if 'specifications' in v), None)

    @staticmethod
    def get_product_specs(product):
        variant_with_spec = SqdcFormatter.find_variant_with_specs(product)
        return None if variant_with_spec is None else variant_with_spec['specifications']

    @staticmethod
    def format_name(product):
        name = product['title']
        specs = SqdcFormatter.get_product_specs(product)
        if specs is not None:
            name = '{} ({})'.format(specs['Strain'], name)
        return name

    @staticmethod
    def format_name_with_type(product):
        name = SqdcFormatter.format_name(product)
        specs = SqdcFormatter.get_product_specs(product)
        if specs is not None:
            name = name + ', ' + specs['CannabisType']
        return name

    @staticmethod
    def format_cbd(product):
        specs = SqdcFormatter.get_product_specs(product)
        if specs is not None:
            cbd_min = float(specs['CBDContentMin'])
            cbd_max = float(specs['CBDContentMax'])
            cbd = '0' if cbd_min == 0 else '{:>4.1f}-{:>4.1f}'.format(cbd_min, cbd_max)
            return cbd

    @staticmethod
    def format_thc(product):
        specs = SqdcFormatter.get_product_specs(product)
        if specs is not None:
            thc_min = float(specs['THCContentMin'])
            thc_max = float(specs['THCContentMax'])
            thc = '0' if thc_min == 0 else '{:>4.1f}-{:>4.1f}'.format(thc_min, thc_max)
            return thc

    @staticmethod
    def format_type(product):
        specs = SqdcFormatter.get_product_specs(product)
        if specs is not None:
            return specs['CannabisType']
        else:
            return None

    @staticmethod
    def build_products_table(products, prepend_with_newline=True):
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
             p['url']] for p in products]
        prefix = '\n' if prepend_with_newline else ''
        return prefix + tabulate(tabulated_data, headers=headers) + '\n'

    @staticmethod
    def format_category(p):
        specs = SqdcFormatter.get_product_specs(p)
        return (specs or {}).get('LevelTwoCategory')
