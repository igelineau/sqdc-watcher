import json
import argparse
import logging
from threading import Event

from lib.formatter import SqdcFormatter
from lib.client import SqdcClient
from lib.watcher import SqdcWatcher


def parse_args():
    parser = argparse.ArgumentParser(description='Watch SQDC products')
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--only-from-cache', action='store_true')
    parser.add_argument('--watch-interval', type=int, default=5, help='watcher execution interval, in minutes.')
    parser.add_argument('--log-level', default='info')
    parser.add_argument('--slack-post-url')
    return parser.parse_args()


log_level_table = {
    'warn': logging.WARN,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

args = parse_args()
logging.basicConfig(level=log_level_table[args.log_level.lower()],
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(levelname)s:%(name)s: %(asctime)s - %(message)s')

if args.watch:
    stop_event = Event()
    watcher = SqdcWatcher(stop_event, args.watch_interval * 60, args.slack_post_url)
    watcher.run()
else:
    # assume display
    if args.only_from_cache:
        products = json.load(open('products.json', 'r'))
    else:
        client = SqdcClient()
        products = client.get_products()
        json.dump(products, open('products.json', 'w+'))

    products_in_stock = [p for p in products if p['in_stock']]
    print(SqdcFormatter.build_products_table(products_in_stock))
