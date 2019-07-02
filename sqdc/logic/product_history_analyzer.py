from typing import List

from datetime import datetime, timedelta

from sqdc.dataobjects.product import Product
from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.productevent import ProductEvent
from sqdc.dto.history_time_accumulator import HistoryTimeAccumulator


class ProductHistoryAnalyzer:
    def __init__(self, product: Product):
        self.product = product

    def calculate_percentage_in_stock(self, history_entries: List[ProductHistory], end_datetime=datetime.now()):
        total_delta = end_datetime - self.product.created

        current_state: ProductEvent
        accumulator = HistoryTimeAccumulator()
        prev_time = self.product.created
        for entry in history_entries:
            current_state = ProductEvent[entry.event.upper()]
            current_delta = entry.timestamp - prev_time
            prev_time = entry.timestamp
            accumulator.add_time(current_delta, current_state == ProductEvent.NOT_IN_STOCK)
        accumulator.add_time(end_datetime - prev_time, self.product.in_stock if len(history_entries) == 0 else current_state == ProductEvent.IN_STOCK)

        percentage_in_stock = (accumulator.time_in_stock / total_delta) * 100
        return percentage_in_stock
