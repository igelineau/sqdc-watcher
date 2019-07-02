class ProductStockDifferences:
    def __init__(self, became_in_stock, became_out_of_stock):
        self.became_out_of_stock = became_out_of_stock
        self.became_in_stock = became_in_stock

    def __repr__(self):
        return f'became in stock: {len(self.became_in_stock)}, became out of stock: {len(self.became_out_of_stock)}'
