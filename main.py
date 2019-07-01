import argparse
import logging
from threading import Event

from lib.formatter import SqdcFormatter
from lib.client import SqdcClient
from lib.watcher import SqdcWatcher
from lib.watcherOptions import WatcherOptions


def parse_args():
    parser = argparse.ArgumentParser(description='Watch SQDC products')
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Monitor periodically the Sqdc website for new available products. If any found, post to Slack if the slack-post-url was provided.')
    parser.add_argument(
        '--only-from-cache',
        action='store_true')
    parser.add_argument(
        '--watch-interval',
        type=int, default=5, help='watcher execution interval, in minutes.')
    parser.add_argument(
        '--log-level',
        default='info')
    parser.add_argument(
        '--slack-post-url',
        help='The URL to a slack incoming webhook that will be used if new products were found while in watch mode.')
    parser.add_argument(
        '--slack-oauth-token',
        help='The Slack OAuth Token that will be used to use the Slack API')
    parser.add_argument(
        '--display-format',
        help='Format of the products displayed in the console.',
        default='table', choices=['list', 'table'])
    parser.add_argument(
        '--slack-port',
        help='The port of the server listening for slack commands',
        default='19019'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Save the products to products-test.json'
    )
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
log_test_indicator = ' [TEST] ' if args.test else ''
logging.basicConfig(level=log_level_table[args.log_level.lower()],
                    datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(levelname)s' + log_test_indicator + ':%(name)s: %(asctime)s - %(message)s')

if args.watch:
    stop_event = Event()
    options = WatcherOptions.default()
    options.slack_post_url = args.slack_post_url
    options.is_test_mode = args.test
    options.display_format = args.display_format
    options.slack_token = args.slack_oauth_token
    options.interval = args.watch_interval
    options.slack_port = int(args.slack_port)

    watcher = SqdcWatcher(stop_event, options)
    watcher.daemon = True
    watcher.start()
else:
    client = SqdcClient()
    products = client.get_products()
    products_in_stock = [p for p in products if p.is_in_stock()]
    print(SqdcFormatter.format_products(products_in_stock, args.display_format))
