from threading import Thread

from .client import SqdcClient
from .formatter import SqdcFormatter
from .product_filters import ProductFilters


class SqdcWatcher(Thread):
    def __init__(self, event, interval=60 * 5):
        Thread.__init__(self)
        self._stopped = event
        self.client = SqdcClient()
        self.interval = interval

    def run(self):
        while not self.stopped.wait(self.interval):
            self.execute_scan()

    def execute_scan(self):
        try:
            products = self.client.get_products()
            products_in_stock = ProductFilters.in_stock(products)
            print(SqdcFormatter.format_product(products_in_stock))

        except:
            print('watcher failed to get products')
