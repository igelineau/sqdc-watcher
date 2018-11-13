import logging
import datetime
from threading import Thread
import traceback

from typing import List
from lib.product import Product
from .client import SqdcClient
from .formatter import SqdcFormatter
from .dbstore import SqdcStore
from .product_filters import ProductFilters

log = logging.getLogger(__name__)


class SqdcWatcher(Thread):
    def __init__(self, event, interval=60 * 5, slack_post_url=""):
        Thread.__init__(self)
        self._stopped = event
        self.client = SqdcClient()
        self.interval = interval
        self.store = SqdcStore()
        self.slack_post_url = slack_post_url

    def run(self):
        log.info('INITIALIZED - interval = {}'.format(self.interval))
        last_saved_products_rel = datetime.datetime.now() - self.store.get_products_last_saved_timestamp()
        print('Last successful execution : {:.0g}m ago'.format(last_saved_products_rel.total_seconds() / 60))
        is_stopping = False
        while not is_stopping:
            self.execute_scan()
            log.info('TASK EXECUTED. Waiting {:.2g} minutes until next execution.'.format(self.interval / 60))
            is_stopping = self._stopped.wait(self.interval)

        log.info('STOPPED')

    def execute_scan(self):
        try:
            products = self.client.get_products()

            products_in_stock = ProductFilters.in_stock(products)
            log.info(SqdcFormatter.build_products_table(products_in_stock))

            prev_products = self.store.get_products()
            new_products = [p for p in self.calculate_new_items(prev_products, products) if p.is_in_stock()]
            if len(new_products) == 0:
                log.info('No new product available')
            else:
                log.info('There are {} new products available since last scan :'.format(len(new_products)))
                log.info(SqdcFormatter.build_products_table(new_products))

                log.info('List of all available products:')
                log.info(SqdcFormatter.build_products_table(products_in_stock))

                log.info('Posting to Slack to announce the good news.')
                self.post_new_products_to_slack(new_products)
                self.store.save_products(products)

        except:
            traceback.format_exc()
            log.error('watcher job execution encountered an error:')
            log.error(traceback.format_exc())

    def post_new_products_to_slack(self, new_products):
        if self.slack_post_url:
            message = '\n'.join(['- ' + SqdcFormatter.format_product(p) for p in new_products])
            self.client.post_to_slack(self.slack_post_url, message)

    @staticmethod
    def calculate_new_items(prev_products: List[Product], cur_products: List[Product]):
        prev_ids = [p.id for p in prev_products]
        cur_ids = [p.id for p in cur_products]
        new_products = [pid
                        for pid in cur_ids
                        if pid not in prev_ids]
        return [p for p in cur_products if p.id in new_products]
