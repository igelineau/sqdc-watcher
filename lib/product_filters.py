from lib.product import Product


class ProductFilters:
    @staticmethod
    def in_stock(products_list):
        return [p for p in products_list if p.is_in_stock()]
