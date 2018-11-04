class ProductFilters:
    @staticmethod
    def in_stock(products_list):
        return [p for p in products_list if p['in_stock']]
