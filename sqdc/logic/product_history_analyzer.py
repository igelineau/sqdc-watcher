import logging
from datetime import datetime, timedelta
from typing import List

from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.product_variant import ProductVariant
from sqdc.dataobjects.productevent import ProductEvent

log = logging.getLogger(__name__)


class ProductHistoryAnalyzer:
    def __init__(self, variant: ProductVariant):
        self.variant = variant

    def calculate_percentage_in_stock(self, product: Product, history_entries: List[ProductHistory], end_datetime=datetime.now()):
        if not product.created and len(history_entries) == 0:
            return 0

        variant_created = self.variant.created
        if not variant_created:
            first_in_stock = ProductHistoryAnalyzer.find_first_event_of_type(history_entries, ProductEvent.IN_STOCK)
            if not first_in_stock:
                return 0
            else:
                variant_created = first_in_stock.timestamp

        total_delta = end_datetime - variant_created
        time_in_stock = timedelta()
        is_in_stock = len(product.variants) > 0
        prev_time = variant_created
        prev_event = (is_in_stock and ProductEvent.IN_STOCK) or ProductEvent.NOT_IN_STOCK

        for entry in history_entries:
            current_in_stock = entry.event == ProductEvent.NOT_IN_STOCK.name.lower()
            just_became_out_of_stock = prev_event == ProductEvent.IN_STOCK and not current_in_stock

            if just_became_out_of_stock:
                time_in_stock += (entry.timestamp - prev_time)

            if just_became_out_of_stock or current_in_stock:
                prev_time = entry.timestamp

            prev_event = ProductEvent[entry.event.upper()]

        if len(history_entries) > 0 and prev_event == ProductEvent.IN_STOCK:
            time_in_stock += (datetime.now() - prev_time)

        percentage_in_stock = (time_in_stock / total_delta) * 100
        return percentage_in_stock

    @staticmethod
    def find_first_event_of_type(entries: List[ProductHistory], evemt: ProductEvent):
        return next(iter([e for e in entries if e.event == evemt.name.lower()]))
