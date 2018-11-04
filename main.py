from tabulate import tabulate
from lib.client import SqdcClient
import json

is_online = False


def format_product(product):
    in_stock_str = 'In stock' if product['in_stock'] else 'Out of stock'
    variants_in_stock = [v for v in product['variants'] if v['in_stock']]
    variants_descriptions = ', '.join(
        [str(float(v['specifications']['GramEquivalent']['Value'])) + ' g' for v in variants_in_stock])
    return '[{}] - {} ({}), quantities available: {}'.format(in_stock_str, product['title'], product['brand'],
                                                             variants_descriptions)


def format_variants_available(product):
    variants_in_stock = [v for v in product['variants'] if v['in_stock']]
    variants_descriptions = ', '.join(
        [str(float(v['specifications']['GramEquivalent']['Value'])) + ' g' for v in variants_in_stock])
    return variants_descriptions


def format_brand_and_supplier(product):
    variant_with_specifications = [v for v in product['variants'] if 'specifications' in v][0]
    brand = product['brand']
    producerName = variant_with_specifications['specifications']['ProducerName']['Value']
    displayString = brand
    if producerName != brand:
        displayString += ' (' + producerName + ')'

    return displayString


def print_products_table(products):
    headers = ['Name', 'In Stock', 'Brand', 'Formats available']
    tabulated_data = [[p['title'], p['in_stock'], format_brand_and_supplier(p), format_variants_available(p)]
                      for p in products]
    print(tabulate(tabulated_data, headers=headers))


client = SqdcClient()

if is_online:
    products = client.get_products()
    json.dump(products, open('products.json', 'w+'))
else:
    products = json.load(open('products.json', 'r'))

in_stock_products = [p for p in products if p['in_stock']]

products_in_stock = [p for p in products if p['in_stock']]
print_products_table(products_in_stock)
# for product in in_stock_products:
#    print(format_product(product))
