import json
import argparse
import logging

from lib.formatter import SqdcFormatter
from lib.client import SqdcClient




def parse_args():
    parser = argparse.ArgumentParser(description='Watch SQDC products')
    parser.add_argument('watch', action='store_true')
    parser.add_argument('--only-from-cache', action='store_true')
    parser.add_argument('--watch-interval', type=int, default=5, help='watcher execution interval, in minutes.')
    return parser.parse_args()

logging.basicConfig(level=logging.INFO)

args = parse_args()
client = SqdcClient()

if args.only_from_cache:
    products = json.load(open('products.json', 'r'))
else:
    products = client.get_products()
    json.dump(products, open('products.json', 'w+'))

products_in_stock = [p for p in products if p['in_stock']]
print(SqdcFormatter.build_products_table(products_in_stock))
