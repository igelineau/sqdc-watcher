import logging
from datetime import datetime
from typing import List

from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.product_variant import ProductVariant
from sqdc.dataobjects.productevent import ProductEvent
from sqdc.dto.history_time_accumulator import HistoryTimeAccumulator

log = logging.getLogger(__name__)


class ProductHistoryAnalyzer:
    def __init__(self, variant: ProductVariant):
        self.variant = variant

    def calculate_percentage_in_stock(self, history_entries: List[ProductHistory], end_datetime=datetime.now()):
        total_delta = end_datetime - self.variant.created

        current_state: ProductEvent
        accumulator = HistoryTimeAccumulator()
        prev_time = self.variant.created
        for entry in history_entries:
            current_state = ProductEvent[entry.event.upper()]
            current_delta = entry.timestamp - prev_time
            prev_time = entry.timestamp
            accumulator.add_time(current_delta, current_state == ProductEvent.NOT_IN_STOCK)
        accumulator.add_time(end_datetime - prev_time, self.variant.in_stock if len(history_entries) == 0 else current_state == ProductEvent.IN_STOCK)

        log.debug(f'total= {total_delta}, time in stock: {accumulator.time_in_stock}')
        percentage_in_stock = (accumulator.time_in_stock / total_delta) * 100
        return percentage_in_stock
