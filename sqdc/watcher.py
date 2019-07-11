import datetime
import logging
import traceback
from threading import Thread, Event
from typing import List

from babel.dates import format_timedelta

from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.productevent import ProductEvent
from sqdc.logic.product_calculator import ProductCalculator, find_by_id
from sqdc.server import SlackEndpointServer
from sqdc.slack_client import SlackClient
from sqdc.watcherOptions import WatcherOptions
from .SqdcStore import SqdcStore
from .formatter import SqdcFormatter
from .product_filters import ProductFilters
from .products_updater import ProductsUpdater

log = logging.getLogger(__name__)

# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class SqdcWatcher(Thread):
    def __init__(self, event: Event, options: WatcherOptions = WatcherOptions.default()):
        Thread.__init__(self)
        self._stopped = event
        self.store = SqdcStore(options.is_test_mode)
        self.products_updater = ProductsUpdater(self.store)
        self.slack_client = SlackClient(options.slack_token)
        self.slack_post_url = options.slack_post_url
        self.display_format = 'table'
        self.is_test = options.is_test_mode
        self.interval = options.interval * 60
        self.display_format = options.display_format
        self.min_duration_between_scans_minutes = 15
        self.no_cache = options.no_cache

        self.slack_server = SlackEndpointServer(options.slack_port, self, self.store)

    def run(self):
        self.store.initialize()
        self.log_initialized_event()
        self.log_notification_rules()

        self.main_loop()
        self.shutdown()

    def main_loop(self):
        is_stopping = False
        while not is_stopping:
            self.execute_scan()
            log.info('TASK EXECUTED. Waiting {:.2g} minutes until next execution.'.format(self.interval / 60))
            is_stopping = self._stopped.wait(self.interval)

    def shutdown(self):
        log.info('Watcher daemon - shutting down...')
        self.slack_server.stop()

    def log_initialized_event(self):
        log.info('INITIALIZED - interval = {}'.format(self.interval))
        app_state = self.store.get_app_state()

        if not app_state.last_scan_timestamp:
            last_scan_relative = 'Never'
        else:
            last_scan_relative = format_timedelta(app_state.last_scan_timestamp - datetime.datetime.now(), add_direction=True)
        log.info(f'Products were last updated {last_scan_relative}')

    def log_notification_rules(self):
        notification_rules = self.store.get_all_notification_rules()
        if len(notification_rules) > 0:
            log.info('loaded {} notification rules:'.format(len(notification_rules)))
            for username, rules in notification_rules.items():
                log.info('To @{}:'.format(username))
                for rule in rules:
                    log.info('  {}'.format(rule.keyword))

    def execute_scan(self):
        try:
            calculator = self.refresh_products()

            all_in_stock = ProductFilters.in_stock(calculator.updated_products)
            log.info('List of all available products:')
            log.info(SqdcFormatter.format_products(all_in_stock, self.display_format))

            became_out_of_stock = calculator.get_became_out_of_stock()
            if len(became_out_of_stock) > 0:
                log.info('Products just became out of stock: ' + ', '.join([f'{p}' for p in became_out_of_stock]))

            became_in_stock = calculator.get_became_in_stock()
            became_in_stock_for_notifications = list(filter(lambda p: self.product_filter_for_notification(p, calculator), became_in_stock))
            nb_ignored_because_recently_notified = len(became_in_stock) - len(became_in_stock_for_notifications)
            if nb_ignored_because_recently_notified > 0:
                log.info(f'{nb_ignored_because_recently_notified} products became in stock, but were filtered - they won\'t be posted to Slack.')

            if len(became_in_stock) == 0:
                log.info(f'No product came back in stock. Total in stock: {len(all_in_stock)}')
            else:
                self.apply_notification_rules(became_in_stock)
                self.add_event_to_products(became_in_stock, ProductEvent.IN_STOCK)
                self.add_event_to_products(became_out_of_stock, ProductEvent.NOT_IN_STOCK)

                log.info('There are {} new products available since last scan (total, {} in stock)'.format(len(became_in_stock), len(all_in_stock)))
                log.info(SqdcFormatter.build_products_table(became_in_stock))

                self.send_in_stock_updates_to_slack_if_needed(calculator.previous_products, became_in_stock_for_notifications)

        except KeyboardInterrupt:
            log.info('CTRL+C pressed. exiting program.')
        except:
            traceback.format_exc()
            log.error('watcher job execution encountered an error:')
            log.error(traceback.format_exc())

    @staticmethod
    def product_filter_for_notification(product: Product, calculator: ProductCalculator):
        return product.category.lower() == 'dried flowers' and calculator.was_product_recently_in_stock(product)

    def refresh_products(self):
        app_state = self.store.get_app_state()
        time_since_refresh = (datetime.datetime.now() - (app_state.last_scan_timestamp or datetime.datetime.min))
        use_cached_products = not self.no_cache and time_since_refresh < datetime.timedelta(minutes=self.min_duration_between_scans_minutes)
        if use_cached_products:
            log.debug('Using cached products')
        else:
            log.debug('Re-fetching products from SQDC API...')

        store_products = self.store.get_products()
        updated_products = self.products_updater.get_products(cached_products=use_cached_products and self.store.get_products())

        calculator = ProductCalculator(
            self.store,
            previous_products=store_products,
            updated_products=updated_products
        )

        became_in_stock = calculator.get_became_in_stock()
        if len(became_in_stock) > 0:
            for p in calculator.updated_products:
                p.is_new = False

            for p in calculator.get_new_products():
                p.is_new = True

        log.info(f'Saving {len(calculator.updated_products)} updated products')
        self.store.save_products(calculator.updated_products)
        became_out_of_stock = calculator.get_became_out_of_stock()
        if len(became_out_of_stock) > 0:
            log.info(f'Saving {len(became_out_of_stock)} products that just became out of stock: ' + ' '.join([str(p) for p in became_out_of_stock]))
            self.store.save_products(became_out_of_stock)

        products_refetched = self.store.get_products()
        for p in products_refetched:
            self.products_updater.update_availability_stats(p)

        return calculator

    def send_in_stock_updates_to_slack_if_needed(self, previous_products: List[Product], new_products_in_stock: List[Product]):
        if len(previous_products) > 0:
            if self.slack_post_url and len(new_products_in_stock) > 0:
                log.info(f'Send Slack notification in channel ({len(new_products_in_stock)} products)')
                message = '\n'.join(['- ' + SqdcFormatter.format_product(p) for p in new_products_in_stock])
                self.products_updater.sqdc_client.post_to_slack(self.slack_post_url, message)
                self.store.mark_products_notified(new_products_in_stock)
        else:
            log.info('First run - not posting new products to Slack.')

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

    def add_event_to_products(self, products: List[Product], event: ProductEvent):
        entries = []
        for product in products:
            for variant in product.variants:
                entries.append(ProductHistory(product_id=product.id, variant_id=variant.id, event=event.name.lower()))
        if len(entries) > 0:
            self.store.add_product_history_entries(entries)
