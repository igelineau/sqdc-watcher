from sqdc.dataobjects.schema import products, metadata, product_history


class ProductsStore:
    def add_history_entry(self, product_id, variant_id, event, quantities):
        insert = product_history.insert()
