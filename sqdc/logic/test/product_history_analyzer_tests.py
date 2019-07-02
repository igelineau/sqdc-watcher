from datetime import datetime, timedelta

from sqdc.dataobjects.product_history import ProductHistory
from sqdc.dataobjects.productevent import ProductEvent
from sqdc.logic.product_history_analyzer import ProductHistoryAnalyzer
from sqdc.logic.test.test_base import TestBase


class HistoryAnalyzerTests(TestBase):

    def test_percentage_in_stock(self):
        product = self.create_product(created=datetime.now() - timedelta(hours=8))

        def create_entry(event: ProductEvent, timestamp: datetime):
            return ProductHistory(product_id=product.id, variant_id=product.variants[0].id, event=event.name.lower(), timestamp=timestamp)

        entries = [
            create_entry(ProductEvent.IN_STOCK, product.created),
            create_entry(ProductEvent.NOT_IN_STOCK, product.created + timedelta(hours=4))
        ]

        analyzer = ProductHistoryAnalyzer(product)
        percentage = analyzer.calculate_percentage_in_stock(entries)

        self.assertAlmostEqual(percentage, 50, 4)