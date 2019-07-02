import logging
import datetime
import signal
import sys
from threading import Thread, Event
import traceback

from typing import List

from lib.server import SlackEndpointServer
from lib.slack_client import SlackClient
from lib.stores.product import Product
from lib.stores.product_history import ProductHistory
from lib.watcherOptions import WatcherOptions
from .client import SqdcClient
from .formatter import SqdcFormatter
from .SqdcStore import SqdcStore
from .product_filters import ProductFilters

log = logging.getLogger(__name__)

# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class SqdcWatcher(Thread):
    def __init__(self, event: Event, options: WatcherOptions = WatcherOptions.default()):
        Thread.__init__(self)
        self._stopped = event
        self.store = SqdcStore(options.is_test_mode)
        self.client = SqdcClient(self.store)
        self.slack_client = SlackClient(options.slack_token)
        self.slack_post_url = options.slack_post_url
        self.display_format = 'table'
        self.is_test = options.is_test_mode
        self.interval = options.interval * 60
        self.display_format = options.display_format

        self.slack_server = SlackEndpointServer(options.slack_port, self, self.store)

    def run(self):
        self.store.initialize()
        log.info('INITIALIZED - interval = {}'.format(self.interval))
        last_saved_products_rel = datetime.datetime.now() - self.store.get_products_last_saved_timestamp()
        print('Products were last updated {}m ago'.format(last_saved_products_rel))

        notification_rules = self.store.get_all_notification_rules()
        if len(notification_rules) > 0:
            log.info('loaded {} notification rules:'.format(len(notification_rules)))
            for username, rules in notification_rules.items():
                log.info('To @{}:'.format(username))
                for rule in rules:
                    log.info('  {}'.format(rule.keyword))

        is_stopping = False
        while not is_stopping:
            self.execute_scan()
            log.info('TASK EXECUTED. Waiting {:.2g} minutes until next execution.'.format(self.interval / 60))
            is_stopping = self._stopped.wait(self.interval)
            if is_stopping:
                print('Watcher daemon - shutting down...')
                self.slack_server.stop()

    def execute_scan(self):
        try:
            products = self.client.get_products()
            products_in_stock = ProductFilters.in_stock(products)

            prev_products = self.store.get_products()
            new_products = self.calculate_new_items(prev_products, products_in_stock)
            vanished_products = self.calculate_new_items(products_in_stock, ProductFilters.in_stock(prev_products))

            log.info('List of all available products:')
            log.info(SqdcFormatter.format_products(products_in_stock, self.display_format))

            if len(new_products) == 0:
                log.info('No new product available')
            else:
                log.info('saving products')
                self.store.save_products(products)

                self.apply_notification_rules(new_products)
                self.add_event_to_products(new_products, 'in_stock')
                self.add_event_to_products(vanished_products, 'out_of_stock')

                log.info('There are {} new products available since last scan :'.format(len(new_products)))
                log.info(SqdcFormatter.build_products_table(new_products))

                if len(prev_products) > 0:
                    log.info('Posting to Slack to announce the good news.')
                    self.post_new_products_to_slack(new_products)
                else:
                    log.info('First run - not posting new products to Slack.')
        except KeyboardInterrupt:
            log.info('CTRL+C pressed. exiting program.')
        except:
            traceback.format_exc()
            log.error('watcher job execution encountered an error:')
            log.error(traceback.format_exc())

    def post_new_products_to_slack(self, new_products: List[Product]):
        if self.slack_post_url:
            message = '\n'.join(['- ' + SqdcFormatter.format_product(p) for p in new_products])
            self.client.post_to_slack(self.slack_post_url, message)

    def handle_in_stock_products(self, products: List[Product]):
        self.store.save_products(products)

    @staticmethod
    def calculate_new_items(prev_products: List[Product], cur_products: List[Product]):
        prev_ids = set([p.id for p in prev_products if p.is_in_stock()])
        cur_ids = set([p.id for p in cur_products if p.is_in_stock()])
        new_products = [pid
                        for pid in cur_ids
                        if pid not in prev_ids]
        return [p for p in cur_products if p.id in new_products]

    def apply_notification_rules(self, products: List[Product]):

        all_rules = self.store.get_all_notification_rules()
        for username, rules in all_rules.items():
            products_found = []
            for product in products:
                for rule in rules:
                    if product.get_specification('Strain').lower().find(rule.keyword.lower()) >= 0:
                        products_found.append(product)
            nb_found = len(products_found)
            if nb_found > 0:
                message = '------------\n' + \
                          '*{} new available products are matching your notification alerts:*\n'.format(nb_found)
                for product in products_found:
                    message += '   - {}\n'.format(SqdcFormatter.format_product(product))
                message += '------------'
                self.slack_client.chat_send_message(message, username)

    def add_event_to_products(self, products: List[Product], event_name: str):
        entries = []
        for product in products:
            for variant in product.variants:
                entries.append(ProductHistory(product_id=product.id, variant_id=variant.id, event=event_name))
        if len(entries) > 0:
            self.store.add_product_history_entries(entries)
